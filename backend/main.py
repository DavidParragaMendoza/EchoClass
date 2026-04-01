from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import logging
from typing import Optional

from transcription import TranscriptionService
from llm_processor import LLMProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EchoClass API", description="🎙️ Transcripción y resumen de clases con IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

transcription_service = TranscriptionService()
llm_processor = LLMProcessor()


class SummaryRequest(BaseModel):
    text: str


@app.on_event("startup")
async def startup_event():
    """Inicializa el servicio de transcripción al arrancar"""
    logger.info("🚀 Iniciando servidor...")
    transcription_service.load_model()
    logger.info("✅ Modelo de transcripción cargado")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpia recursos al cerrar"""
    logger.info("🔄 Liberando recursos...")
    transcription_service.unload_model()
    logger.info("✅ Recursos liberados")


@app.get("/")
async def root():
    return {
        "message": "🎙️ EchoClass API - Transcripción de clases con IA",
        "status": "running",
        "endpoints": {
            "websocket": "/ws",
            "summarize": "/summarize",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Verifica el estado del servidor y los servicios"""
    return {
        "status": "healthy",
        "transcription_model": "loaded" if transcription_service.model else "not_loaded",
        "ollama_available": await llm_processor.check_ollama_status()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para recibir audio en tiempo real y enviar transcripción
    """
    await websocket.accept()
    logger.info("📡 Cliente WebSocket conectado")
    
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            
            if len(audio_data) > 0:
                logger.info(f"📥 Recibido audio: {len(audio_data)} bytes")
                try:
                    text = await transcription_service.transcribe_chunk(audio_data)
                    
                    if text and text.strip():
                        await websocket.send_json({
                            "type": "transcription",
                            "text": text
                        })
                        logger.info(f"📝 Transcrito: {text[:50]}...")
                        consecutive_errors = 0  # Reset en caso de éxito
                    else:
                        logger.debug("⚠️ No se detectó voz en este chunk")
                        
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"❌ Error al transcribir ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    # Solo notificar al cliente si hay muchos errores consecutivos
                    if consecutive_errors >= max_consecutive_errors:
                        await websocket.send_json({
                            "type": "warning",
                            "message": "Problemas al procesar audio. Intenta hablar más claro o más fuerte."
                        })
                        consecutive_errors = 0  # Reset después de notificar
                    
    except WebSocketDisconnect:
        logger.info("🔌 Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Error del servidor: {str(e)}"
            })
        except:
            pass


@app.post("/summarize")
async def summarize_text(request: SummaryRequest):
    """
    Genera un resumen estructurado usando Ollama
    
    IMPORTANTE: Se libera el modelo Whisper antes de cargar Ollama
    para evitar sobrecarga de RAM
    """
    try:
        if not request.text or len(request.text.strip()) < 50:
            return JSONResponse(
                status_code=400,
                content={"error": "El texto es demasiado corto para resumir"}
            )
        
        logger.info("🧠 Liberando modelo Whisper...")
        transcription_service.unload_model()
        
        logger.info("🤖 Generando resumen con Ollama...")
        summary = await llm_processor.generate_summary(request.text)
        
        logger.info("✅ Resumen generado exitosamente")
        logger.info("🔄 Recargando modelo Whisper...")
        transcription_service.load_model()
        
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"❌ Error al generar resumen: {e}")
        transcription_service.load_model()
        return JSONResponse(
            status_code=500,
            content={"error": f"Error al generar resumen: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
