"""
Excepciones personalizadas de la aplicación
"""


class EchoClassError(Exception):
    """Excepción base de EchoClass"""
    pass


class TranscriptionError(EchoClassError):
    """Error durante la transcripción de audio"""
    pass


class ModelNotLoadedError(TranscriptionError):
    """El modelo de transcripción no está cargado"""
    pass


class AudioProcessingError(TranscriptionError):
    """Error al procesar datos de audio"""
    pass


class SummarizationError(EchoClassError):
    """Error durante la generación de resumen"""
    pass


class OllamaConnectionError(SummarizationError):
    """No se puede conectar con Ollama"""
    pass


class OllamaModelError(SummarizationError):
    """El modelo de Ollama no está disponible"""
    pass


class ConfigurationError(EchoClassError):
    """Error en la configuración de la aplicación"""
    pass
