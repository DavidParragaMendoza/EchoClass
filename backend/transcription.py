import io
import tempfile
import logging
from typing import Optional
from faster_whisper import WhisperModel
import numpy as np

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Servicio de transcripción usando faster-whisper
    Optimizado para máxima precisión en español
    """
    
    def __init__(self, model_size: str = "small"):
        """
        Inicializa el servicio de transcripción
        
        Args:
            model_size: Tamaño del modelo ('tiny', 'base', 'small', 'medium', 'large')
                       'small' ofrece buen equilibrio precisión/velocidad para CPU
        """
        self.model_size = model_size
        self.model: Optional[WhisperModel] = None
        self.device = "cpu"
        self.compute_type = "int8"
        
        logger.info(f"🎙️ Servicio de transcripción configurado con modelo '{model_size}'")
    
    def load_model(self):
        """Carga el modelo Whisper en memoria"""
        if self.model is None:
            try:
                logger.info(f"⏳ Cargando modelo Whisper '{self.model_size}'... (puede tomar 1-2 minutos)")
                
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    cpu_threads=8,  # Más hilos para mejor rendimiento
                    num_workers=2
                )
                
                logger.info(f"✅ Modelo '{self.model_size}' cargado exitosamente")
                
            except Exception as e:
                logger.error(f"❌ Error al cargar modelo: {e}")
                raise
    
    def unload_model(self):
        """Libera el modelo de la memoria para reducir consumo de RAM"""
        if self.model is not None:
            logger.info("🔄 Liberando modelo Whisper de memoria...")
            del self.model
            self.model = None
            
            import gc
            gc.collect()
            
            logger.info("✅ Modelo Whisper liberado")
    
    async def transcribe_chunk(self, audio_bytes: bytes) -> str:
        """
        Transcribe un fragmento de audio
        
        Args:
            audio_bytes: Bytes de audio en formato WebM/Opus
            
        Returns:
            Texto transcrito
        """
        if self.model is None:
            self.load_model()
        
        # Validar tamaño mínimo de audio (5KB mínimo para evitar chunks vacíos)
        if len(audio_bytes) < 5000:
            logger.debug(f"⚠️ Chunk muy pequeño ({len(audio_bytes)} bytes), omitiendo...")
            return ""
        
        tmp_webm_path = None
        tmp_wav_path = None
        
        try:
            import os
            import subprocess
            
            # Guardar los bytes de audio a un archivo temporal WebM
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_webm_path = tmp_file.name
            
            # Convertir WebM a WAV usando FFmpeg para mejor compatibilidad
            tmp_wav_path = tmp_webm_path.replace(".webm", ".wav")
            
            # Comando FFmpeg para convertir WebM a WAV
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", tmp_webm_path,
                "-ar", "16000",  # Sample rate 16kHz
                "-ac", "1",       # Mono
                "-f", "wav",
                "-y",             # Sobrescribir sin preguntar
                tmp_wav_path,
                "-loglevel", "error"
            ]
            
            # Ejecutar conversión
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Error en conversión FFmpeg: {result.stderr.decode()}")
                return ""
            
            # Verificar que el archivo WAV existe y tiene contenido
            if not os.path.exists(tmp_wav_path) or os.path.getsize(tmp_wav_path) < 1000:
                logger.warning("⚠️ Archivo WAV vacío o no generado")
                return ""
            
            # Transcribir desde el archivo WAV con parámetros optimizados para precisión
            segments, info = self.model.transcribe(
                tmp_wav_path,
                language="es",
                beam_size=5,          # Mayor beam = más precisión (era 1)
                best_of=3,            # Evaluar 3 candidatos (era 1)
                temperature=0.0,      # Sin aleatoriedad para máxima precisión
                patience=1.5,         # Más paciencia en la búsqueda
                condition_on_previous_text=False,  # Evitar propagación de errores
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=300,   # Detectar pausas más cortas
                    speech_pad_ms=250              # Más contexto alrededor del habla
                )
            )
            
            text = " ".join([segment.text for segment in segments])
            
            return text.strip()
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Timeout en conversión de audio")
            return ""
        except Exception as e:
            logger.error(f"❌ Error en transcripción: {e}")
            return ""
        finally:
            # Limpiar archivos temporales
            import os
            if tmp_webm_path and os.path.exists(tmp_webm_path):
                try:
                    os.unlink(tmp_webm_path)
                except:
                    pass
            if tmp_wav_path and os.path.exists(tmp_wav_path):
                try:
                    os.unlink(tmp_wav_path)
                except:
                    pass
    
    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe un archivo de audio completo
        
        Args:
            audio_path: Ruta al archivo de audio
            
        Returns:
            Texto transcrito completo
        """
        if self.model is None:
            self.load_model()
        
        try:
            logger.info(f"📄 Transcribiendo archivo: {audio_path}")
            
            segments, info = self.model.transcribe(
                audio_path,
                language="es",
                beam_size=5,
                vad_filter=True
            )
            
            text = " ".join([segment.text for segment in segments])
            
            logger.info(f"✅ Transcripción completada ({len(text)} caracteres)")
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Error al transcribir archivo: {e}")
            raise
