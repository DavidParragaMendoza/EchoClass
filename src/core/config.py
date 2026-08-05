"""
Configuración centralizada de la aplicación
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WhisperConfig:
    """
    Configuración del modelo Whisper para transcripción.
    
    Modelos disponibles (model_size):
      - "tiny"     (~39M params, VRAM/RAM <1GB)  : Ultrarrápido, precisión básica.
      - "base"     (~74M params, VRAM/RAM ~1GB)  : Muy rápido, ideal para CPU en laptops modestas.
      - "small"    (~244M params, VRAM/RAM ~2GB) : Excelente balance velocidad/precisión recomendado para CPU.
      - "medium"   (~769M params, VRAM/RAM ~5GB) : Alta precisión, recomendado para CPU potentes o GPU gama media.
      - "large-v3" (~1550M params, VRAM/RAM ~10GB): Máxima calidad de transcripción, recomendado para GPU CUDA.
    
    Dispositivo (device):
      - "cuda" : Usar GPU NVIDIA (si no hay GPU, el sistema hará fallback automático a CPU).
      - "cpu"  : Fuerza el uso de procesador (CPU).
    
    Tipo de computación (compute_type):
      - Para GPU (cuda): "float16", "int8_float16", "float32"
      - Para CPU       : "int8" (recomendado para velocidad en CPU), "float32"
    """
    model_size: str = "small"  # Modelo por defecto (si estás en CPU sin GPU, te recomendamos cambiar a "small" o "base")
    language: str = "es"
    device: str = "cuda"  # Intenta GPU NVIDIA por defecto con fallback automático a CPU si no se detecta CUDA
    cpu_threads: int = 4
    num_workers: int = 2
    compute_type: str = "float16"  # Se ajustará a "int8" automáticamente si se cambia a CPU en el fallback


@dataclass
class OllamaConfig:
    """Configuración de Ollama para resúmenes"""
    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"
    timeout: int = 300  # 5 minutos por chunk


@dataclass
class ServerConfig:
    """Configuración del servidor"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


@dataclass
class Settings:
    """Configuración global de la aplicación"""
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Carga configuración desde variables de entorno"""
        default_whisper = WhisperConfig()
        return cls(
            whisper=WhisperConfig(
                model_size=os.getenv("WHISPER_MODEL", default_whisper.model_size),
                language=os.getenv("WHISPER_LANGUAGE", default_whisper.language),
                device=os.getenv("WHISPER_DEVICE", default_whisper.device),
                cpu_threads=int(os.getenv("WHISPER_CPU_THREADS", str(default_whisper.cpu_threads))),
                num_workers=int(os.getenv("WHISPER_NUM_WORKERS", str(default_whisper.num_workers))),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", default_whisper.compute_type),
            ),
            ollama=OllamaConfig(
                model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ),
            server=ServerConfig(
                host=os.getenv("SERVER_HOST", "0.0.0.0"),
                port=int(os.getenv("SERVER_PORT", "8000")),
                debug=os.getenv("DEBUG", "false").lower() == "true",
            ),
        )


# Instancia global de configuración
settings = Settings.from_env()
