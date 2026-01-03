from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Telegram LLM Bot"
    version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./data/bot.db"
    
    # Security
    encryption_key: Optional[str] = None  # Generate with: from cryptography.fernet import Fernet; Fernet.generate_key()
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Paths
    data_dir: str = "./data"
    frontend_dir: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
