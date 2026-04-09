"""
Configuración centralizada de la aplicación
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WhisperConfig:
    """Configuración del modelo Whisper para transcripción"""
    model_size: str = "large"  # tiny, base, small, medium, large
    language: str = "es"
    cpu_threads: int = 4
    num_workers: int = 2
    compute_type: str = "float16"  # máxima precisión en GPU NVIDIA
    device: str = "cuda"


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
        return cls(
            whisper=WhisperConfig(
                model_size=os.getenv("WHISPER_MODEL", "large"),
                language=os.getenv("WHISPER_LANGUAGE", "es"),
                cpu_threads=int(os.getenv("WHISPER_CPU_THREADS", "4")),
                num_workers=int(os.getenv("WHISPER_NUM_WORKERS", "2")),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
                device=os.getenv("WHISPER_DEVICE", "cuda"),
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
