"""
Adaptador de Ollama para generación de resúmenes

Implementa el puerto SummarizationPort usando Ollama local
"""
import re
import asyncio
from typing import List, AsyncIterator, Tuple
from dataclasses import dataclass

import aiohttp

from src.core.config import settings
from src.core.logger import setup_logger
from src.core.exceptions import (
    SummarizationError,
    OllamaConnectionError,
    OllamaModelError
)
from src.domain.interfaces import SummarizationPort

logger = setup_logger("ollama")


@dataclass
class ChunkProgress:
    """Progreso del procesamiento de chunks"""
    current_chunk: int
    total_chunks: int
    phase: str  # "chunking", "summarizing", "consolidating"
    message: str


class OllamaAdapter(SummarizationPort):
    """
    Adaptador de Ollama para generación de resúmenes con LLM local.
    Soporta chunking para transcripciones largas con progreso.
    """
    
    # Límites para Ollama con context de 4K tokens (~16K caracteres)
    # Prompt usa ~800 tokens, respuesta ~500 tokens = quedan ~2700 tokens para texto
    # ~4 caracteres por token = ~10,000 chars máx, pero usamos menos para velocidad
    MAX_CONTEXT_CHARS = 2800    # ~700 tokens - procesa sin dividir
    CHUNK_SIZE_CHARS = 1800     # ~450 tokens por chunk - reduce timeouts
    MAX_SUMMARIES_PER_BATCH = 3
    MAX_BATCH_INPUT_CHARS = 3800
    MAX_CONSOLIDATION_ROUNDS = 8
    
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None
    ):
        """
        Inicializa el adaptador de Ollama
        
        Args:
            model: Nombre del modelo (ej: qwen2.5:7b, qwen2.5:3b)
            base_url: URL base de Ollama
            timeout: Timeout en segundos para requests
        """
        config = settings.ollama
        
        self.model = model or config.model
        self.base_url = base_url or config.base_url
        self.timeout = timeout or config.timeout
        
        self.api_url = f"{self.base_url}/api/generate"
        
        logger.info(f"🤖 Adaptador Ollama configurado: modelo='{self.model}'")
    
    async def is_available(self) -> bool:
        """Verifica si Ollama está ejecutándose"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo en uso"""
        return self.model
    
    def calculate_chunks(self, text: str) -> Tuple[List[str], int]:
        """
        Calcula los chunks necesarios para el texto
        
        Returns:
            Tuple de (lista de chunks, total de chunks)
        """
        text_length = len(text)
        
        if text_length <= self.MAX_CONTEXT_CHARS:
            return [text], 1
        
        chunks = self._split_into_chunks(text)
        return chunks, len(chunks)
    
    async def generate_summary(self, text: str) -> str:
        """
        Genera un resumen estructurado del texto.
        Si es muy largo, divide en chunks y consolida.
        
        Args:
            text: Texto a resumir
        
        Returns:
            Resumen en formato Markdown
        """
        # Usar el generador con progreso pero solo retornar el resultado final
        final_summary = ""
        async for progress, result in self.generate_summary_with_progress(text):
            if result:
                final_summary = result
        return final_summary
    
    async def generate_summary_with_progress(
        self, 
        text: str
    ) -> AsyncIterator[Tuple[ChunkProgress, str | None]]:
        """
        Genera resumen con progreso en tiempo real.
        
        Yields:
            Tuplas de (progreso, resultado parcial o None)
        """
        text_length = len(text)
        logger.info(f"📊 Longitud de transcripción: {text_length:,} caracteres")
        
        # Fase 1: Calcular chunks
        yield ChunkProgress(0, 0, "analyzing", f"Analizando texto ({text_length:,} caracteres)..."), None
        
        chunks, total_chunks = self.calculate_chunks(text)
        
        if total_chunks == 1:
            yield ChunkProgress(1, 1, "summarizing", "Texto cabe en contexto, generando resumen..."), None
            summary = await self._generate_single_summary(text)
            yield ChunkProgress(1, 1, "completed", "✅ Resumen completado"), summary
            return
        
        # Fase 2: Informar división
        yield ChunkProgress(
            0, total_chunks, "chunking", 
            f"Texto muy largo. Dividido en {total_chunks} partes para procesar..."
        ), None
        
        # Fase 3: Resumir cada chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            yield ChunkProgress(
                i, total_chunks, "summarizing",
                f"Resumiendo parte {i} de {total_chunks}..."
            ), None
            
            summary = await self._summarize_chunk(chunk, i, total_chunks)
            chunk_summaries.append(summary)
            
            yield ChunkProgress(
                i, total_chunks, "summarizing",
                f"✓ Parte {i}/{total_chunks} completada"
            ), None
        
        # Fase 4: Consolidar
        yield ChunkProgress(
            total_chunks, total_chunks, "consolidating",
            "Consolidando resúmenes parciales en resumen final..."
        ), None
        
        final_summary = await self._consolidate_summaries(chunk_summaries)
        
        yield ChunkProgress(
            total_chunks, total_chunks, "completed",
            f"✅ Resumen completado ({total_chunks} partes procesadas)"
        ), final_summary
    
    async def _generate_single_summary(self, text: str) -> str:
        """Genera resumen de texto que cabe en contexto"""
        prompt = self._build_summary_prompt(text)
        return await self._call_ollama(prompt, max_tokens=2500)
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Divide texto en chunks respetando oraciones"""
        chunks = []
        current_chunk = ""
        
        # Dividir por oraciones
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Si una oración individual excede el límite, dividirla por palabras
            if len(sentence) > self.CHUNK_SIZE_CHARS:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._split_long_segment(sentence))
                continue
            
            # Si agregar esta oración excede el límite
            if len(current_chunk) + len(sentence) > self.CHUNK_SIZE_CHARS and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Agregar último chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_segment(self, text: str) -> List[str]:
        """Divide segmentos largos por palabras para evitar chunks gigantes."""
        words = text.split()
        if not words:
            return []
        
        chunks: List[str] = []
        current = ""
        
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= self.CHUNK_SIZE_CHARS:
                current = candidate
                continue
            
            if current:
                chunks.append(current)
                current = word
                continue
            
            # Palabra individual extremadamente larga: hard split
            for i in range(0, len(word), self.CHUNK_SIZE_CHARS):
                piece = word[i:i + self.CHUNK_SIZE_CHARS]
                if piece:
                    chunks.append(piece)
        
        if current:
            chunks.append(current)
        
        return chunks
    
    async def _summarize_chunk(self, chunk: str, num: int, total: int) -> str:
        """Genera resumen parcial de un chunk"""
        prompt = f"""Eres un asistente que resume clases académicas.

Estás procesando la PARTE {num} de {total} de una clase larga.

Resume esta sección identificando:
- Conceptos principales tratados
- Explicaciones importantes
- Ejemplos o casos mencionados
- Tareas o puntos de acción

TRANSCRIPCIÓN (Parte {num}/{total}):

{chunk}

---

Genera un resumen conciso pero completo de esta sección en español:"""
        
        return await self._call_ollama(prompt, max_tokens=650)
    
    async def _consolidate_summaries(self, summaries: List[str]) -> str:
        """
        Consolida múltiples resúmenes en uno final.
        Si hay muchos resúmenes, usa consolidación jerárquica.
        """
        if not summaries:
            raise SummarizationError("No hay resúmenes parciales para consolidar")
        
        # Si hay un solo resumen parcial, solo formatearlo en plantilla final
        if len(summaries) == 1:
            return await self._consolidate_with_retry(summaries, is_final=True)
        
        logger.info(
            f"📊 Consolidación jerárquica: {len(summaries)} resúmenes "
            f"(máx {self.MAX_SUMMARIES_PER_BATCH} por batch)"
        )
        
        current_summaries = summaries
        round_num = 1
        
        while len(current_summaries) > 1:
            if round_num > self.MAX_CONSOLIDATION_ROUNDS:
                raise SummarizationError(
                    "No se pudo consolidar en un número razonable de rondas"
                )
            
            if self._can_finalize_in_one_call(current_summaries):
                logger.info(f"✨ Consolidación final de {len(current_summaries)} resúmenes")
                return await self._consolidate_with_retry(current_summaries, is_final=True)
            
            batches = self._build_consolidation_batches(current_summaries)
            logger.info(
                f"🔄 Ronda {round_num}: {len(current_summaries)} resúmenes "
                f"→ {len(batches)} batches"
            )
            
            # Consolidar cada batch
            new_summaries = []
            for i, batch in enumerate(batches, 1):
                logger.info(f"  → Batch {i}/{len(batches)}...")
                if len(batch) == 1:
                    new_summaries.append(batch[0])
                    continue
                
                consolidated = await self._consolidate_with_retry(batch, is_final=False)
                new_summaries.append(consolidated.strip())
            
            current_summaries = new_summaries
            round_num += 1
        
        # Garantiza formato final consistente aunque quede un resumen intermedio
        logger.info("✨ Formateando resumen final")
        return await self._consolidate_with_retry(current_summaries, is_final=True)
    
    def _build_consolidation_batches(self, summaries: List[str]) -> List[List[str]]:
        """Arma batches pequeños por cantidad y tamaño total de texto."""
        batches: List[List[str]] = []
        current_batch: List[str] = []
        current_chars = 0
        
        for summary in summaries:
            estimate_chars = len(summary) + 50  # separadores/etiquetas
            exceeds_count = len(current_batch) >= self.MAX_SUMMARIES_PER_BATCH
            exceeds_chars = (current_chars + estimate_chars) > self.MAX_BATCH_INPUT_CHARS
            
            if current_batch and (exceeds_count or exceeds_chars):
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            
            current_batch.append(summary)
            current_chars += estimate_chars
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _can_finalize_in_one_call(self, summaries: List[str]) -> bool:
        """Indica si el lote de resúmenes cabe en una consolidación final."""
        if len(summaries) > self.MAX_SUMMARIES_PER_BATCH:
            return False
        
        total_chars = sum(len(summary) + 50 for summary in summaries)
        return total_chars <= self.MAX_BATCH_INPUT_CHARS
    
    async def _consolidate_with_retry(self, summaries: List[str], is_final: bool) -> str:
        """
        Consolida con fallback recursivo:
        si hay timeout, divide en sublotes más pequeños automáticamente.
        """
        try:
            return await self._consolidate_batch(summaries, is_final=is_final)
        except SummarizationError as e:
            timed_out = "Timeout" in str(e)
            if not timed_out or len(summaries) <= 1:
                raise
            
            logger.warning(
                "⏱️ Timeout consolidando %s secciones. Reintentando en sublotes...",
                len(summaries)
            )
            
            midpoint = len(summaries) // 2
            left = summaries[:midpoint]
            right = summaries[midpoint:]
            
            left_summary = await self._consolidate_with_retry(left, is_final=False)
            right_summary = await self._consolidate_with_retry(right, is_final=False)
            
            return await self._consolidate_with_retry(
                [left_summary, right_summary],
                is_final=is_final
            )
    
    async def _consolidate_batch(self, summaries: List[str], is_final: bool) -> str:
        """Consolida un batch pequeño de resúmenes"""
        combined = "\n\n---\n\n".join(
            [f"**SECCIÓN {i+1}:**\n{s}" for i, s in enumerate(summaries)]
        )
        
        if is_final:
            prompt = f"""Eres un asistente experto en resumir clases académicas.

Consolida estas secciones en un único resumen final, claro y breve.
No inventes contenido ni repitas ideas.

{combined}

---

Devuelve Markdown con esta estructura:

## Resumen:
[1-2 líneas con la idea central de la clase]

## Claves:
- [Punto clave 1]
- [Punto clave 2]
- [Punto clave 3]

## Decisión/impacto:
[Conclusión principal, implicación práctica o decisión tomada]

## Siguiente paso:
[Acción concreta recomendada para continuar]

Máximo ~350 palabras."""
        else:
            prompt = f"""Combina estas secciones en un resumen intermedio orientado a síntesis ejecutiva.
No inventes datos.

{combined}

---

Devuelve Markdown breve con:
- Resumen (idea central)
- Claves (3-5 puntos)
- Decisión/impacto
- Siguiente paso

Máximo ~220 palabras."""
        
        return await self._call_ollama(prompt, max_tokens=750 if is_final else 450)
    
    async def _call_ollama(self, prompt: str, max_tokens: int = 2000) -> str:
        """Llama a Ollama y devuelve la respuesta"""
        try:
            logger.info(f"🔗 Conectando a Ollama ({self.model})...")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                }
                
                async with session.post(
                    self.api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Ollama error {response.status}: {error_text}")
                        raise OllamaModelError(f"Ollama respondió con error: {error_text}")
                    
                    result = await response.json()
                    summary = result.get("response", "")
                    
                    if not summary:
                        raise OllamaModelError("Ollama devolvió respuesta vacía")
                    
                    logger.info(f"✅ Respuesta recibida ({len(summary)} caracteres)")
                    return summary.strip()
                    
        except aiohttp.ClientConnectorError as e:
            error_msg = f"No se pudo conectar con Ollama. ¿Está ejecutándose 'ollama serve'?"
            logger.error(f"❌ {error_msg}")
            raise OllamaConnectionError(error_msg)
        except asyncio.TimeoutError:
            error_msg = f"Timeout: Ollama tardó más de {self.timeout}s en responder. Intenta con chunks más pequeños."
            logger.error(f"❌ {error_msg}")
            raise SummarizationError(error_msg)
        except aiohttp.ClientError as e:
            raise SummarizationError(f"Error de red con Ollama: {e}")
    
    def _build_summary_prompt(self, transcription: str) -> str:
        """Construye el prompt para resumen completo"""
        return f"""Eres un asistente especializado en resumir clases académicas.

A continuación se presenta la transcripción de una clase. Genera un resumen estructurado en formato Markdown:

## Resumen:
[1-2 líneas con la idea central de la clase]

## Claves:
- [Punto clave 1]
- [Punto clave 2]
- [Punto clave 3]
[Incluye de 3 a 5 puntos concretos]

## Decisión/impacto:
[Conclusión principal, implicación práctica o decisión tomada]

## Siguiente paso:
[Acción concreta recomendada para continuar]

---

**TRANSCRIPCIÓN:**

{transcription}

---

**IMPORTANTE:**
- Sé conciso pero completo
- Mantén la estructura Markdown
- Si no hay información para alguna sección, omítela
- Usa lenguaje claro y académico
- Resalta conceptos técnicos en **negrita**
- No organices por subtemas como eje principal"""
