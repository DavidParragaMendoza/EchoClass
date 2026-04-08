"""
EchoClass - Punto de entrada de la aplicación

Ensambla todos los componentes y configura el servidor FastAPI
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.logger import setup_logger
from src.api.routes.health import router as api_router
from src.api.websockets.transcription_ws import websocket_endpoint
from src.api.dependencies import get_transcription_service

logger = setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejo del ciclo de vida de la aplicación.
    Carga el modelo al inicio y lo libera al cerrar.
    """
    # Startup
    logger.info("🚀 Iniciando EchoClass...")
    
    transcription_service = get_transcription_service()
    transcription_service.initialize()
    
    logger.info("✅ EchoClass listo")
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando EchoClass...")
    transcription_service.shutdown()
    logger.info("✅ EchoClass cerrado")


def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.
    
    Returns:
        Aplicación FastAPI configurada
    """
    app = FastAPI(
        title="EchoClass API",
        description="🎙️ Transcripción y resumen de clases con IA",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rutas API
    app.include_router(api_router)
    
    # WebSocket
    app.websocket("/ws")(websocket_endpoint)
    
    # Archivos estáticos (frontend)
    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
        logger.info(f"📁 Frontend montado desde: {static_path}")
    else:
        logger.warning(f"⚠️ Directorio static no encontrado: {static_path}")
    
    return app


# Crear instancia de la aplicación
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.debug,
        log_level="info"
    )
