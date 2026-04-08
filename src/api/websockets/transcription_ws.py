"""
WebSocket handler para transcripción en tiempo real
"""
from fastapi import WebSocket, WebSocketDisconnect

from src.api.dependencies import get_transcription_service
from src.core.logger import setup_logger
from src.core.exceptions import TranscriptionError

logger = setup_logger("websocket")


class TranscriptionWebSocket:
    """
    Handler de WebSocket para transcripción en tiempo real.
    Recibe audio en chunks y envía transcripciones.
    """
    
    MAX_CONSECUTIVE_ERRORS = 3
    
    def __init__(self):
        self._transcription_service = get_transcription_service()
    
    async def handle(self, websocket: WebSocket) -> None:
        """
        Maneja la conexión WebSocket
        
        Args:
            websocket: Conexión WebSocket del cliente
        """
        await websocket.accept()
        logger.info("📡 Cliente WebSocket conectado")
        
        consecutive_errors = 0
        
        try:
            while True:
                # Recibir audio
                audio_data = await websocket.receive_bytes()
                
                if len(audio_data) > 0:
                    logger.info(f"📥 Recibido audio: {len(audio_data)} bytes")
                    
                    try:
                        # Transcribir
                        text = await self._transcription_service.transcribe_audio(audio_data)
                        
                        if text and text.strip():
                            await websocket.send_json({
                                "type": "transcription",
                                "text": text
                            })
                            logger.info(f"📝 Transcrito: {text[:50]}...")
                            consecutive_errors = 0
                        else:
                            logger.debug("⚠️ No se detectó voz en este chunk")
                            
                    except TranscriptionError as e:
                        consecutive_errors += 1
                        logger.error(f"❌ Error de transcripción ({consecutive_errors}): {e}")
                        
                        if consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                            await websocket.send_json({
                                "type": "warning",
                                "message": "Problemas al procesar audio. Intenta hablar más claro."
                            })
                            consecutive_errors = 0
                            
                    except Exception as e:
                        consecutive_errors += 1
                        logger.error(f"❌ Error inesperado ({consecutive_errors}): {e}")
                        
                        if consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                            await websocket.send_json({
                                "type": "warning",
                                "message": "Error al procesar audio. Verificando servicio..."
                            })
                            consecutive_errors = 0
                            
        except WebSocketDisconnect:
            logger.info("🔌 Cliente WebSocket desconectado")
            
        except Exception as e:
            logger.error(f"❌ Error en WebSocket: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error del servidor: {str(e)}"
                })
            except Exception:
                pass


# Instancia singleton del handler
ws_handler = TranscriptionWebSocket()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Endpoint WebSocket para transcripción en tiempo real.
    
    Args:
        websocket: Conexión WebSocket
    """
    await ws_handler.handle(websocket)
