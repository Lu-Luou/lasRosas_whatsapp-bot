"""
Backend FastAPI para bot de WhatsApp con evolution-api
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
import logging
from datetime import datetime

from config import settings
from models import (
    Message, MessageType, MessageAttachment,
    ConversationState, BotResponse
)
from flows import get_flow_node, get_initial_flow
from json_flow import json_flow_service, load_json_flow_or_raise
from storage import storage
from utils import log_message

# Configurar logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ciclo de vida de la aplicación."""
    logger.info("Backend iniciando en %s:%s", settings.backend_host, settings.backend_port)
    logger.info("Storage path: %s", settings.storage_path)
    logger.info("Attachments path: %s", settings.attachments_path)
    try:
        flow = load_json_flow_or_raise()
        logger.info("JSON flow cargado: %s (%s nodos)", flow.flow_id, len(flow.nodes))
    except RuntimeError as err:
        # No bloquea el backend actual, pero deja registro para corregir el JSON.
        logger.warning("No se pudo cargar bot_flow.json: %s", err)
    yield


app = FastAPI(
    title="Las Rosas WhatsApp Bot",
    description="Backend para bot de WhatsApp integrado con evolution-api",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Verificar salud del backend"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Las Rosas WhatsApp Bot",
        "json_flow": json_flow_service.summary(),
    }


@app.post("/webhook/message")
async def receive_message(message: Message):
    """
    Endpoint para recibir mensajes de evolution-api
    
    El webhook de evolution-api enviará mensajes aquí
    """
    try:
        sender_jid = message.sender_jid
        log_message(sender_jid, f"Mensaje recibido: {message.message_text[:50]}...", "receive")
        
        # Obtener o crear estado de conversación
        conversation_state = storage.get_conversation(sender_jid)
        
        if not conversation_state:
            # Nueva conversación
            flow_node = get_initial_flow()
            conversation_state = ConversationState(
                sender_jid=sender_jid,
                current_flow_id=flow_node.id,
                current_node_id=flow_node.id,
            )
            log_message(sender_jid, "Nueva conversación iniciada", "info")
        
        # Procesar el mensaje según el tipo
        if message.message_type == MessageType.LOCATION and message.location:
            conversation_state.location_collected = message.location
            log_message(sender_jid, f"Ubicación recibida: {message.location.latitude}, {message.location.longitude}", "location")
        
        if message.attachments:
            for attachment in message.attachments:
                conversation_state.attachments_collected.append(attachment)
                log_message(sender_jid, f"Adjunto recibido: {attachment.file_name}", "attachment")
        
        # Guardar texto libre en metadata si está permitido
        if message.message_text:
            current_flow = get_flow_node(conversation_state.current_node_id)
            if current_flow and current_flow.allow_free_text:
                if "user_inputs" not in conversation_state.metadata:
                    conversation_state.metadata["user_inputs"] = []
                conversation_state.metadata["user_inputs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "text": message.message_text
                })
        
        # Procesar opción seleccionada (si es un menú)
        next_node_id = None
        if message.message_text.strip().isdigit():
            option_num = int(message.message_text.strip())
            current_flow = get_flow_node(conversation_state.current_node_id)
            
            if current_flow and current_flow.options:
                # Buscar la opción por número (1-indexed)
                if 0 < option_num <= len(current_flow.options):
                    selected_option = current_flow.options[option_num - 1]
                    next_node_id = selected_option.next_flow_id
                    log_message(sender_jid, f"Opción seleccionada: {option_num} - {selected_option.label}", "choice")
        
        # Obtener el siguiente nodo
        if next_node_id:
            next_node = get_flow_node(next_node_id)
            if next_node:
                conversation_state.current_node_id = next_node.id
                conversation_state.current_flow_id = next_node_id
        
        # Guardar estado actualizado
        storage.save_conversation(conversation_state)
        
        # Generar respuesta
        current_flow = get_flow_node(conversation_state.current_node_id)
        bot_response = BotResponse(
            sender_jid=sender_jid,
            message=current_flow.message,
            options=current_flow.options,
            expects_attachment=current_flow.allow_attachments,
            expects_location=current_flow.allow_location,
            expects_free_text=current_flow.allow_free_text,
            next_flow_id=current_flow.id,
        )
        
        log_message(sender_jid, f"Respondiendo con flow: {current_flow.id}", "response")
        
        return {
            "status": "processed",
            "response": bot_response.model_dump(),
        }
        
    except Exception as e:
        logger.exception("Error processing message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/webhook/attachment")
async def receive_attachment(
    sender_jid: str,
    file: UploadFile = File(...),
    message_type: str = "document"
):
    """
    Endpoint para recibir adjuntos
    """
    try:
        log_message(sender_jid, f"Adjunto recibido: {file.filename}", "attachment")
        
        # Leer contenido del archivo
        content = await file.read()

        attachment_type = MessageType.DOCUMENT
        if message_type.lower() == MessageType.IMAGE.value:
            attachment_type = MessageType.IMAGE
        elif message_type.lower() == MessageType.LOCATION.value:
            attachment_type = MessageType.LOCATION
        
        # Crear modelo de adjunto
        attachment = MessageAttachment(
            type=attachment_type,
            file_name=file.filename,
            mime_type=file.content_type,
            size=len(content),
            file_path=""  # Se actualiza al guardar
        )
        
        # Guardar archivo
        file_path = storage.save_attachment(sender_jid, attachment, content)
        
        # Obtener conversación y agregar adjunto
        conversation_state = storage.get_conversation(sender_jid)
        if conversation_state:
            conversation_state.attachments_collected = [
                *conversation_state.attachments_collected,
                attachment,
            ]
            storage.save_conversation(conversation_state)
        
        return {
            "status": "saved",
            "file_path": file_path,
            "filename": file.filename,
        }
        
    except Exception as e:
        logger.exception("Error processing attachment")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/conversation/{sender_jid}")
async def get_conversation(sender_jid: str):
    """
    Obtener el estado actual de una conversación
    """
    try:
        state = storage.get_conversation(sender_jid)
        
        if not state:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "status": "found",
            "conversation": state.model_dump(mode='json'),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving conversation")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/conversation/{sender_jid}")
async def reset_conversation(sender_jid: str):
    """
    Reiniciar una conversación
    """
    try:
        storage.delete_conversation(sender_jid)
        log_message(sender_jid, "Conversación reiniciada", "reset")
        
        return {
            "status": "reset",
            "message": "Conversation reset successfully"
        }
        
    except Exception as e:
        logger.exception("Error resetting conversation")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/flows")
async def list_flows():
    """
    Listar todos los flujos disponibles (para debug)
    """
    from flows import FLOW_NODES
    return {
        "flows": [
            {
                "id": node.id,
                "name": node.name,
                "options_count": len(node.options)
            }
            for node in FLOW_NODES.values()
        ]
    }


@app.get("/flow-json")
async def get_json_flow():
    """Obtiene el flujo JSON actualmente cargado."""
    flow = json_flow_service.get()
    if not flow:
        raise HTTPException(
            status_code=404,
            detail="JSON flow not loaded. Verifica bot_flow.json y reinicia o usa /flow-json/reload",
        )

    return {
        "status": "loaded",
        "flow": flow.model_dump(mode="json"),
    }


@app.post("/flow-json/reload")
async def reload_json_flow():
    """Recarga bot_flow.json sin reiniciar el servidor."""
    try:
        flow = json_flow_service.reload()
        return {
            "status": "reloaded",
            "summary": json_flow_service.summary(),
            "flow_id": flow.flow_id,
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        log_level=settings.log_level.lower()
    )
