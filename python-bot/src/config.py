from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Evolution API
    evolution_api_url: str = "http://localhost:8080"
    evolution_api_key: str = "your_api_key_here"
    
    # Backend
    backend_port: int = 8000
    backend_host: str = "0.0.0.0"
    
    # Storage
    storage_path: str = "./data"
    attachments_path: str = "./data/attachments"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def storage_dir(self) -> Path:
        """Retorna la ruta de almacenamiento como Path"""
        return Path(self.storage_path)
    
    @property
    def attachments_dir(self) -> Path:
        """Retorna la ruta de adjuntos como Path"""
        return Path(self.attachments_path)


settings = Settings()
