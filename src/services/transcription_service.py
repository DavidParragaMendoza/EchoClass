"""
Servicio de Transcripción - Caso de Uso

Orquesta la transcripción de audio usando el adaptador de Whisper
"""
from typing import Optional

from src.core.logger import setup_logger
from src.domain.interfaces import TranscriptionPort
from src.infrastructure.ai.whisper_adapter import WhisperAdapter

logger = setup_logger("transcription_service")


class TranscriptionService:
    """
    Servicio de aplicación para transcripción de audio.
    Actúa como intermediario entre la API y el adaptador de Whisper.
    """
    
    def __init__(self, transcription_adapter: Optional[TranscriptionPort] = None):
        """
        Inicializa el servicio de transcripción
        
        Args:
            transcription_adapter: Adaptador de transcripción (por defecto WhisperAdapter)
        """
        self._adapter = transcription_adapter or WhisperAdapter()
        logger.info("📝 Servicio de transcripción inicializado")
    
    @property
    def adapter(self) -> TranscriptionPort:
        """Retorna el adaptador de transcripción"""
        return self._adapter
    
    def initialize(self) -> None:
        """Inicializa el servicio cargando el modelo"""
        logger.info("🚀 Inicializando servicio de transcripción...")
        self._adapter.load_model()
        logger.info("✅ Servicio de transcripción listo")
    
    def shutdown(self) -> None:
        """Libera recursos del servicio"""
        logger.info("🔄 Cerrando servicio de transcripción...")
        self._adapter.unload_model()
        logger.info("✅ Servicio de transcripción cerrado")
    
    def is_ready(self) -> bool:
        """Indica si el servicio está listo para transcribir"""
        return self._adapter.is_loaded()
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe datos de audio a texto
        
        Args:
            audio_data: Datos de audio en formato WebM/Opus
        
        Returns:
            Texto transcrito o None si no se detectó voz
        """
        if not self.is_ready():
            logger.warning("⚠️ Modelo no cargado, cargando automáticamente...")
            self.initialize()
        
        return await self._adapter.transcribe(audio_data)
    
    def free_memory(self) -> None:
        """Libera el modelo de memoria temporalmente"""
        self._adapter.unload_model()
    
    def reload(self) -> None:
        """Recarga el modelo en memoria"""
        self._adapter.load_model()
