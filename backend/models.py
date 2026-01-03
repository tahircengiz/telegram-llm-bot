from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from .database import Base


class LLMProvider(Base):
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # 'ollama', 'openai', 'gemini'
    enabled = Column(Boolean, default=False)
    active = Column(Boolean, default=False)  # Only one can be active
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OllamaConfig(Base):
    __tablename__ = "ollama_config"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), unique=True)
    base_url = Column(String(255), nullable=False, default="http://ollama.ollama.svc.cluster.local:11434")
    model = Column(String(100), nullable=False, default="qwen:1.8b")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(Text, default="Sen Türkçe konuşan bir akıllı ev asistanısın.")


class OpenAIConfig(Base):
    __tablename__ = "openai_config"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), unique=True)
    api_key = Column(String(255), nullable=False)  # Will be encrypted
    model = Column(String(100), default="gpt-4o-mini")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(Text, default="Sen Türkçe konuşan bir akıllı ev asistanısın.")


class GeminiConfig(Base):
    __tablename__ = "gemini_config"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"), unique=True)
    api_key = Column(String(255), nullable=False)  # Will be encrypted
    model = Column(String(100), default="gemini-pro")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    system_prompt = Column(Text, default="Sen Türkçe konuşan bir akıllı ev asistanısın.")


class TelegramConfig(Base):
    __tablename__ = "telegram_config"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_token = Column(String(255), nullable=False)  # Will be encrypted
    allowed_chat_ids = Column(Text, default="[]")  # JSON array
    rate_limit = Column(Integer, default=10)  # messages per minute
    enabled = Column(Boolean, default=True)


class HomeAssistantConfig(Base):
    __tablename__ = "ha_config"
    
    id = Column(Integer, primary_key=True, index=True)
    base_url = Column(String(255), default="http://192.168.7.200:8123")
    api_token = Column(String(255), nullable=True)  # Encrypted, optional for now
    exposed_entities = Column(Text, default="[]")  # JSON array of entity IDs
    dry_run_mode = Column(Boolean, default=True)


class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(50))
    user_message = Column(Text)
    bot_response = Column(Text)
    llm_provider = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
