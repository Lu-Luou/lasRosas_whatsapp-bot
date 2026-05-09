from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class MessageType(str, Enum):
    """Tipos de mensajes"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"


class MessageAttachment(BaseModel):
    """Modelo para adjuntos de mensajes"""
    type: MessageType
    file_path: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None


class Location(BaseModel):
    """Modelo para ubicación"""
    latitude: float
    longitude: float
    address: Optional[str] = None
    accuracy: Optional[float] = None


class Message(BaseModel):
    """Modelo para mensajes desde/hacia WhatsApp"""
    sender_jid: str  # ID del remitente (WhatsApp)
    message_text: str
    message_type: MessageType = MessageType.TEXT
    attachments: List[MessageAttachment] = Field(default_factory=list)
    location: Optional[Location] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class FlowOption(BaseModel):
    """Modelo para opciones en un flujo"""
    id: str
    label: str
    next_flow_id: Optional[str] = None


class FlowNode(BaseModel):
    """Modelo para nodos del flujo"""
    id: str
    name: str
    message: str
    options: List[FlowOption] = Field(default_factory=list)
    allow_attachments: bool = False
    allow_location: bool = False
    allow_free_text: bool = False


class ConversationState(BaseModel):
    """Modelo para el estado de una conversación"""
    sender_jid: str
    current_flow_id: str
    current_node_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments_collected: List[MessageAttachment] = Field(default_factory=list)
    location_collected: Optional[Location] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BotResponse(BaseModel):
    """Modelo para la respuesta del bot"""
    sender_jid: str
    message: str
    options: List[FlowOption] = Field(default_factory=list)
    expects_attachment: bool = False
    expects_location: bool = False
    expects_free_text: bool = False
    next_flow_id: Optional[str] = None
