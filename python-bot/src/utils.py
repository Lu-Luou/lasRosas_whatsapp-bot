"""Funciones auxiliares"""

import logging
from typing import Optional

from config import settings

# Configurar logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


def log_message(sender_jid: str, message: str, message_type: str = "info"):
    """Registra un mensaje en los logs"""
    logger.info("[%s] (%s): %s", sender_jid, message_type, message)


def format_flow_message(node_message: str, options: list = None) -> str:
    """Formatea un mensaje del flujo con sus opciones"""
    formatted = node_message
    
    if options:
        formatted += "\n\n"
        for option in options:
            formatted += f"{option.label}\n"
    
    return formatted


def parse_user_choice(message_text: str) -> Optional[str]:
    """Intenta parsear una opción numérica del usuario"""
    import re

    match = re.search(r'\d+', message_text.strip())
    if match:
        return match.group()
    return None


def parse_location_from_message(message_data: dict) -> Optional[dict]:
    """Extrae información de ubicación del mensaje de evolution-api"""
    if "location" in message_data:
        loc = message_data["location"]
        return {
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "accuracy": loc.get("accuracy"),
        }
    return None
