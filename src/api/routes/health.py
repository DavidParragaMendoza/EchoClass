"""
Rutas REST de la API

Endpoints para health check, información y resúmenes
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from src.api.dependencies import get_transcription_service, get_summarization_service
from src.services.transcription_service import TranscriptionService
from src.services.summarization_service import SummarizationService
from src.core.exceptions import SummarizationError
from src.core.logger import setup_logger

logger = setup_logger("routes")

router = APIRouter()


class SummaryRequest(BaseModel):
    """Request para generar resumen"""
    text: str


class SummaryResponse(BaseModel):
    """Response con el resumen generado"""
    summary: str


@router.get("/api")
async def root():
    """Información de la API"""
    return {
        "message": "🎙️ EchoClass API - Transcripción de clases con IA",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "websocket": "/ws",
            "summarize": "/summarize",
            "summarize_stream": "/summarize/stream",
            "health": "/health"
        }
    }


@router.get("/health")
async def health_check(
    transcription_svc: TranscriptionService = Depends(get_transcription_service),
    summarization_svc: SummarizationService = Depends(get_summarization_service)
):
    """
    Verifica el estado del servidor y los servicios
    
    Returns:
        Estado de salud de todos los componentes
    """
    ollama_available = await summarization_svc.is_available()
    
    return {
        "status": "healthy",
        "services": {
            "transcription": {
                "status": "loaded" if transcription_svc.is_ready() else "not_loaded"
            },
            "summarization": {
                "status": "available" if ollama_available else "unavailable",
                "model": summarization_svc.get_model_name()
            }
        }
    }


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_text(
    request: SummaryRequest,
    transcription_svc: TranscriptionService = Depends(get_transcription_service),
    summarization_svc: SummarizationService = Depends(get_summarization_service)
):
    """
    Genera un resumen estructurado del texto (sin progreso)
    """
    try:
        logger.info("🧠 Liberando modelo Whisper para optimizar RAM...")
        transcription_svc.free_memory()
        
        logger.info("🤖 Generando resumen con Ollama...")
        summary = await summarization_svc.generate_summary(request.text)
        
        logger.info("🔄 Recargando modelo Whisper...")
        transcription_svc.reload()
        
        return SummaryResponse(summary=summary.summary_text)
        
    except SummarizationError as e:
        logger.error(f"❌ Error de resumen: {e}")
        try:
            transcription_svc.reload()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        try:
            transcription_svc.reload()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error al generar resumen: {str(e)}")


@router.post("/summarize/stream")
async def summarize_text_stream(
    request: SummaryRequest,
    transcription_svc: TranscriptionService = Depends(get_transcription_service),
    summarization_svc: SummarizationService = Depends(get_summarization_service)
):
    """
    Genera un resumen con progreso en tiempo real via Server-Sent Events.
    
    El cliente recibe eventos con el formato:
    - {"type": "progress", "phase": "...", "current": N, "total": M, "message": "..."}
    - {"type": "complete", "summary": "..."}
    - {"type": "error", "message": "..."}
    """
    
    async def generate_events():
        try:
            # Liberar memoria
            yield f"data: {json.dumps({'type': 'progress', 'phase': 'preparing', 'message': 'Liberando memoria...'})}\n\n"
            transcription_svc.free_memory()
            
            # Verificar disponibilidad
            if not await summarization_svc.is_available():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Ollama no está disponible'})}\n\n"
                return
            
            # Generar resumen con progreso
            async for progress, result in summarization_svc.generate_summary_with_progress(request.text):
                event_data = {
                    "type": "progress",
                    "phase": progress.phase,
                    "current": progress.current_chunk,
                    "total": progress.total_chunks,
                    "message": progress.message
                }
                yield f"data: {json.dumps(event_data)}\n\n"
                
                if result:
                    yield f"data: {json.dumps({'type': 'complete', 'summary': result})}\n\n"
            
        except SummarizationError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"❌ Error en stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Error inesperado: {str(e)}'})}\n\n"
        finally:
            try:
                transcription_svc.reload()
                yield f"data: {json.dumps({'type': 'progress', 'phase': 'cleanup', 'message': 'Modelo de transcripción recargado'})}\n\n"
            except Exception:
                pass
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
