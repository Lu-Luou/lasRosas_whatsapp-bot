"""Gestión de almacenamiento de conversaciones y adjuntos"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from models import ConversationState, MessageAttachment
from config import settings


class ConversationStorage:
    """Gestor de almacenamiento de conversaciones"""
    
    def __init__(self):
        self.storage_dir = settings.storage_dir
        self.attachments_dir = settings.attachments_dir
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Crea los directorios si no existen"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_conversation_file(self, sender_jid: str) -> Path:
        """Obtiene la ruta del archivo de conversación"""
        return self.storage_dir / f"{sender_jid}_conversation.json"
    
    def get_conversation(self, sender_jid: str) -> Optional[ConversationState]:
        """Obtiene el estado de una conversación"""
        file_path = self._get_conversation_file(sender_jid)
        
        if not file_path.exists():
            return None

        data = json.loads(file_path.read_text(encoding='utf-8'))
        return ConversationState(**data)
    
    def save_conversation(self, state: ConversationState):
        """Guarda el estado de una conversación"""
        file_path = self._get_conversation_file(state.sender_jid)

        state.updated_at = datetime.now()
        file_path.write_text(
            json.dumps(state.model_dump(mode='json'), indent=2, default=str),
            encoding='utf-8',
        )
    
    def save_attachment(self, sender_jid: str, attachment: MessageAttachment, file_data: bytes) -> str:
        """Guarda un archivo adjunto"""
        # Crear directorio para el usuario si no existe
        user_dir = self.attachments_dir / sender_jid
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{attachment.file_name or 'attachment'}"
        file_path = user_dir / file_name

        file_path.write_bytes(file_data)

        # Actualizar la ruta en el modelo
        attachment.file_path = str(file_path)
        return str(file_path)
    
    def list_attachments(self, sender_jid: str) -> list[MessageAttachment]:
        """Lista todos los adjuntos de un usuario"""
        user_dir = self.attachments_dir / sender_jid
        
        if not user_dir.exists():
            return []
        
        attachments = []

        for file_path in user_dir.iterdir():
            if file_path.is_file():
                attachment = MessageAttachment(
                    type="document",  # Por defecto
                    file_path=str(file_path),
                    file_name=file_path.name,
                    size=file_path.stat().st_size,
                )
                attachments.append(attachment)
        
        return attachments
    
    def delete_conversation(self, sender_jid: str):
        """Elimina el archivo de conversación"""
        file_path = self._get_conversation_file(sender_jid)

        if file_path.exists():
            file_path.unlink()


# Instancia global
storage = ConversationStorage()
