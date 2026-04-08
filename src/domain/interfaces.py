"""
Interfaces (Puertos) - Contratos para los adaptadores
"""
from abc import ABC, abstractmethod
from typing import Optional


class TranscriptionPort(ABC):
    """
    Puerto para servicios de transcripción de audio.
    Define el contrato que deben implementar los adaptadores de transcripción.
    """
    
    @abstractmethod
    def load_model(self) -> None:
        """Carga el modelo de transcripción en memoria"""
        pass
    
    @abstractmethod
    def unload_model(self) -> None:
        """Descarga el modelo de memoria para liberar recursos"""
        pass
    
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe datos de audio a texto
        
        Args:
            audio_data: Datos de audio en formato bytes (WebM/Opus)
        
        Returns:
            Texto transcrito o None si no se detectó voz
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """Indica si el modelo está cargado en memoria"""
        pass


class SummarizationPort(ABC):
    """
    Puerto para servicios de generación de resúmenes.
    Define el contrato que deben implementar los adaptadores de LLM.
    """
    
    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        """
        Genera un resumen estructurado del texto
        
        Args:
            text: Texto a resumir (transcripción de clase)
        
        Returns:
            Resumen estructurado
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica si el servicio de LLM está disponible"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Retorna el nombre del modelo en uso"""
        pass
