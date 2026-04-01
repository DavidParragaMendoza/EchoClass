import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LLMProcessor:
    """
    Procesador de resúmenes usando Ollama local
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """
        Inicializa el procesador LLM
        
        Args:
            base_url: URL base de Ollama
            model: Modelo a usar (llama3, mistral, gemma, etc.)
        """
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
        
        logger.info(f"🤖 Procesador LLM configurado con modelo '{model}'")
    
    async def check_ollama_status(self) -> bool:
        """Verifica si Ollama está ejecutándose"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=5) as response:
                    return response.status == 200
        except:
            return False
    
    async def generate_summary(self, transcription: str) -> str:
        """
        Genera un resumen estructurado de la transcripción
        
        Args:
            transcription: Texto transcrito de la clase
            
        Returns:
            Resumen en formato Markdown
        """
        prompt = self._build_prompt(transcription)
        
        try:
            logger.info(f"🤖 Enviando {len(transcription)} caracteres a Ollama...")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 2000
                    }
                }
                
                async with session.post(
                    self.api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Error de Ollama: {error_text}")
                    
                    result = await response.json()
                    summary = result.get("response", "")
                    
                    if not summary:
                        raise Exception("Ollama devolvió una respuesta vacía")
                    
                    logger.info(f"✅ Resumen generado ({len(summary)} caracteres)")
                    return summary.strip()
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Error de conexión con Ollama: {e}")
            raise Exception(
                "No se pudo conectar con Ollama. "
                "Verifica que esté ejecutándose con 'ollama serve'"
            )
        except Exception as e:
            logger.error(f"❌ Error al generar resumen: {e}")
            raise
    
    def _build_prompt(self, transcription: str) -> str:
        """
        Construye el prompt para el modelo
        
        Args:
            transcription: Transcripción de la clase
            
        Returns:
            Prompt estructurado
        """
        return f"""Eres un asistente especializado en resumir clases académicas. 

A continuación se presenta la transcripción de una clase. Tu tarea es generar un resumen estructurado y completo en formato Markdown con la siguiente estructura:

# 📚 Título de la Clase
[Determina un título descriptivo basado en el contenido]

## 🎯 Tema Principal
[Resumen breve del tema central de la clase en 2-3 líneas]

## 📝 Conceptos Clave
- **Concepto 1**: Explicación breve
- **Concepto 2**: Explicación breve
- **Concepto 3**: Explicación breve
[Lista todos los conceptos importantes mencionados]

## 🔍 Desarrollo de Contenido
[Resumen detallado del desarrollo de la clase, organizando los temas en orden lógico]

## ✅ Tareas y Acciones Pendientes
- [ ] Tarea 1
- [ ] Tarea 2
[Si se mencionaron tareas, ejercicios o lecturas pendientes]

## 💡 Puntos Destacados
- Punto importante 1
- Punto importante 2
[Ideas clave que el estudiante debe recordar]

## 📖 Referencias Mencionadas
[Si se mencionaron libros, artículos, videos o recursos]

---

**TRANSCRIPCIÓN DE LA CLASE:**

{transcription}

---

**IMPORTANTE:**
- Sé conciso pero completo
- Mantén la estructura de Markdown indicada
- Si no hay información para alguna sección, omítela
- Usa lenguaje claro y académico
- Resalta los conceptos técnicos importantes en **negrita**
"""
