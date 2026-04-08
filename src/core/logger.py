"""
Configuración centralizada de logging
"""
import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "echoclass",
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configura y retorna un logger con formato consistente
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        format_string: Formato personalizado del log
    
    Returns:
        Logger configurado
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(format_string, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
    
    logger.setLevel(level)
    return logger


# Logger principal de la aplicación
logger = setup_logger()
