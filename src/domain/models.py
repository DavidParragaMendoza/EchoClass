"""
Modelos del dominio - Entidades del negocio
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class SessionStatus(Enum):
    """Estados posibles de una sesión de transcripción"""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class TranscriptionSegment:
    """Segmento individual de transcripción"""
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: Optional[float] = None
    
    def __str__(self) -> str:
        return self.text


@dataclass
class TranscriptionSession:
    """Sesión completa de transcripción"""
    id: str
    segments: List[TranscriptionSegment] = field(default_factory=list)
    status: SessionStatus = SessionStatus.IDLE
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    def add_segment(self, text: str, confidence: Optional[float] = None) -> None:
        """Agrega un nuevo segmento de transcripción"""
        segment = TranscriptionSegment(text=text, confidence=confidence)
        self.segments.append(segment)
    
    def get_full_text(self) -> str:
        """Retorna todo el texto transcrito concatenado"""
        return " ".join(str(segment) for segment in self.segments)
    
    def start(self) -> None:
        """Inicia la sesión"""
        self.status = SessionStatus.RECORDING
        self.started_at = datetime.now()
    
    def stop(self) -> None:
        """Detiene la sesión"""
        self.status = SessionStatus.COMPLETED
        self.ended_at = datetime.now()


@dataclass
class Summary:
    """Resumen generado por IA"""
    id: str
    source_text: str
    summary_text: str
    model_used: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_markdown(self) -> str:
        """Exporta el resumen en formato Markdown"""
        return f"""# Resumen de Clase

**Generado:** {self.created_at.strftime("%Y-%m-%d %H:%M")}
**Modelo:** {self.model_used}

---

{self.summary_text}
"""
    
    def to_plain_text(self) -> str:
        """Exporta el resumen en texto plano"""
        return f"""RESUMEN DE CLASE
Generado: {self.created_at.strftime("%Y-%m-%d %H:%M")}

{self.summary_text}
"""
