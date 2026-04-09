"""
Adaptador de Whisper para transcripción de audio

Implementa el puerto TranscriptionPort usando faster-whisper
"""
import gc
import os
import subprocess
import tempfile
from typing import Optional

from faster_whisper import WhisperModel

from src.core.config import settings
from src.core.logger import setup_logger
from src.core.exceptions import (
    TranscriptionError,
    ModelNotLoadedError,
    AudioProcessingError
)
from src.domain.interfaces import TranscriptionPort

logger = setup_logger("whisper")


class WhisperAdapter(TranscriptionPort):
    """
    Adaptador de faster-whisper para transcripción de audio.
    Optimizado para máxima precisión en español con CPU.
    """
    
    def __init__(
        self,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        cpu_threads: Optional[int] = None,
        compute_type: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Inicializa el adaptador de Whisper
        
        Args:
            model_size: Tamaño del modelo (tiny, base, small, medium, large)
            language: Idioma para transcripción
            cpu_threads: Número de hilos de CPU
            compute_type: Tipo de computación (int8, float16, etc.)
            device: Dispositivo de inferencia (cpu, cuda)
        """
        config = settings.whisper
        
        self.model_size = model_size or config.model_size
        self.language = language or config.language
        self.cpu_threads = cpu_threads or config.cpu_threads
        self.compute_type = compute_type or config.compute_type
        self.device = device or config.device
        self.num_workers = config.num_workers
        
        self._model: Optional[WhisperModel] = None
        
        logger.info(f"🎙️ Adaptador Whisper configurado: modelo='{self.model_size}', idioma='{self.language}'")
    
    def load_model(self) -> None:
        """Carga el modelo Whisper en memoria"""
        if self._model is not None:
            logger.debug("Modelo ya está cargado")
            return
        
        try:
            logger.info(f"⏳ Cargando modelo Whisper '{self.model_size}'...")
            
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                num_workers=self.num_workers
            )
            
            logger.info(f"✅ Modelo '{self.model_size}' cargado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error al cargar modelo: {e}")
            raise TranscriptionError(f"No se pudo cargar el modelo Whisper: {e}")
    
    def unload_model(self) -> None:
        """Libera el modelo de memoria"""
        if self._model is None:
            return
        
        logger.info("🔄 Liberando modelo Whisper de memoria...")
        
        del self._model
        self._model = None
        gc.collect()
        
        logger.info("✅ Modelo Whisper liberado")
    
    def is_loaded(self) -> bool:
        """Indica si el modelo está cargado"""
        return self._model is not None
    
    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe datos de audio a texto
        
        Args:
            audio_data: Datos de audio en formato WebM/Opus
        
        Returns:
            Texto transcrito o None si no se detectó voz
        """
        if not self.is_loaded():
            raise ModelNotLoadedError("El modelo Whisper no está cargado")
        
        # Validar tamaño mínimo
        if len(audio_data) < 5000:
            logger.debug(f"⚠️ Chunk muy pequeño ({len(audio_data)} bytes), omitiendo...")
            return None
        
        tmp_webm_path = None
        tmp_wav_path = None
        
        try:
            # Guardar audio temporal
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_webm_path = tmp_file.name
            
            # Convertir WebM a WAV
            tmp_wav_path = tmp_webm_path.replace(".webm", ".wav")
            
            if not self._convert_to_wav(tmp_webm_path, tmp_wav_path):
                return None
            
            # Transcribir
            segments, info = self._model.transcribe(
                tmp_wav_path,
                language=self.language,
                beam_size=5,
                best_of=3,
                temperature=0.0,
                patience=1.5,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,
                    speech_pad_ms=250
                )
            )
            
            text = " ".join([segment.text for segment in segments])
            return text.strip() if text.strip() else None
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout en conversión de audio")
            return None
        except Exception as e:
            logger.error(f"❌ Error en transcripción: {e}")
            raise AudioProcessingError(f"Error al procesar audio: {e}")
        finally:
            self._cleanup_temp_files(tmp_webm_path, tmp_wav_path)
    
    def _convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convierte audio WebM a WAV usando FFmpeg"""
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", input_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-f", "wav",
                    "-y",
                    output_path,
                    "-loglevel", "error"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Error FFmpeg: {result.stderr.decode()}")
                return False
            
            if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
                logger.warning("⚠️ Archivo WAV vacío o no generado")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout en conversión FFmpeg")
            return False
    
    def _cleanup_temp_files(self, *paths: Optional[str]) -> None:
        """Limpia archivos temporales"""
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass
