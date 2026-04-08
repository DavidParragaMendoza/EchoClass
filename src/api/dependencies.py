"""
Inyección de dependencias para la API

Configura y provee instancias de servicios a los endpoints
"""
from functools import lru_cache

from src.services.transcription_service import TranscriptionService
from src.services.summarization_service import SummarizationService


@lru_cache()
def get_transcription_service() -> TranscriptionService:
    """
    Retorna instancia singleton del servicio de transcripción.
    
    Returns:
        TranscriptionService configurado
    """
    return TranscriptionService()


@lru_cache()
def get_summarization_service() -> SummarizationService:
    """
    Retorna instancia singleton del servicio de resúmenes.
    
    Returns:
        SummarizationService configurado
    """
    return SummarizationService()
