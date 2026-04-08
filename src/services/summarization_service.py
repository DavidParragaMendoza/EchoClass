"""
Servicio de Resúmenes - Caso de Uso

Orquesta la generación de resúmenes usando el adaptador de Ollama
"""
from typing import Optional, AsyncIterator, Tuple
from datetime import datetime
import uuid

from src.core.logger import setup_logger
from src.core.exceptions import SummarizationError
from src.domain.interfaces import SummarizationPort
from src.domain.models import Summary
from src.infrastructure.ai.ollama_adapter import OllamaAdapter, ChunkProgress

logger = setup_logger("summarization_service")


class SummarizationService:
    """
    Servicio de aplicación para generación de resúmenes.
    Actúa como intermediario entre la API y el adaptador de Ollama.
    """
    
    MIN_TEXT_LENGTH = 50  # Mínimo de caracteres para generar resumen
    
    def __init__(self, summarization_adapter: Optional[SummarizationPort] = None):
        """
        Inicializa el servicio de resúmenes
        
        Args:
            summarization_adapter: Adaptador de LLM (por defecto OllamaAdapter)
        """
        self._adapter: OllamaAdapter = summarization_adapter or OllamaAdapter()
        logger.info("🧠 Servicio de resúmenes inicializado")
    
    @property
    def adapter(self) -> OllamaAdapter:
        """Retorna el adaptador de LLM"""
        return self._adapter
    
    async def is_available(self) -> bool:
        """Verifica si el servicio de LLM está disponible"""
        return await self._adapter.is_available()
    
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo en uso"""
        return self._adapter.get_model_name()
    
    async def generate_summary(self, text: str) -> Summary:
        """
        Genera un resumen estructurado del texto
        
        Args:
            text: Texto a resumir (transcripción de clase)
        
        Returns:
            Objeto Summary con el resumen generado
        
        Raises:
            SummarizationError: Si el texto es muy corto o hay error
        """
        self._validate_text(text)
        
        if not await self.is_available():
            raise SummarizationError(
                "Ollama no está disponible. ¿Está ejecutándose 'ollama serve'?"
            )
        
        logger.info(f"📊 Generando resumen ({len(text)} caracteres)...")
        
        summary_text = await self._adapter.generate_summary(text)
        
        summary = Summary(
            id=str(uuid.uuid4()),
            source_text=text,
            summary_text=summary_text,
            model_used=self.get_model_name()
        )
        
        logger.info(f"✅ Resumen generado exitosamente")
        return summary
    
    async def generate_summary_with_progress(
        self, 
        text: str
    ) -> AsyncIterator[Tuple[ChunkProgress, str | None]]:
        """
        Genera resumen con progreso en tiempo real.
        
        Args:
            text: Texto a resumir
        
        Yields:
            Tuplas de (ChunkProgress, resultado parcial o None)
        """
        self._validate_text(text)
        
        async for progress, result in self._adapter.generate_summary_with_progress(text):
            yield progress, result
    
    def _validate_text(self, text: str) -> None:
        """Valida que el texto sea válido para resumir"""
        if not text or len(text.strip()) < self.MIN_TEXT_LENGTH:
            raise SummarizationError(
                f"El texto es demasiado corto para resumir (mínimo {self.MIN_TEXT_LENGTH} caracteres)"
            )
    
    async def generate_summary_text(self, text: str) -> str:
        """
        Genera solo el texto del resumen (sin objeto Summary)
        
        Args:
            text: Texto a resumir
        
        Returns:
            Texto del resumen
        """
        summary = await self.generate_summary(text)
        return summary.summary_text
