from pydantic import BaseModel, Field
from typing import Optional


# LLM Provider Schemas
class LLMProviderBase(BaseModel):
    name: str
    enabled: bool = False
    active: bool = False


class LLMProviderResponse(LLMProviderBase):
    id: int
    
    class Config:
        from_attributes = True


# Ollama Schemas
class OllamaConfigBase(BaseModel):
    base_url: str = Field(default="http://ollama.ollama.svc.cluster.local:11434")
    model: str = Field(default="qwen:1.8b")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    system_prompt: Optional[str] = "Sen Türkçe konuşan bir akıllı ev asistanısın."


class OllamaConfigUpdate(OllamaConfigBase):
    pass


class OllamaConfigResponse(OllamaConfigBase):
    id: int
    provider_id: int
    
    class Config:
        from_attributes = True


# OpenAI Schemas
class OpenAIConfigBase(BaseModel):
    api_key: str
    model: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    system_prompt: Optional[str] = "Sen Türkçe konuşan bir akıllı ev asistanısın."


class OpenAIConfigUpdate(OpenAIConfigBase):
    pass


class OpenAIConfigResponse(BaseModel):
    id: int
    provider_id: int
    api_key: str = "***"  # Masked
    model: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    
    class Config:
        from_attributes = True


# Gemini Schemas
class GeminiConfigBase(BaseModel):
    api_key: str
    model: str = Field(default="gemini-pro")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=100, le=4000)
    system_prompt: Optional[str] = "Sen Türkçe konuşan bir akıllı ev asistanısın."


class GeminiConfigUpdate(GeminiConfigBase):
    pass


class GeminiConfigResponse(BaseModel):
    id: int
    provider_id: int
    api_key: str = "***"  # Masked
    model: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str]
    
    class Config:
        from_attributes = True


# Test Response
class TestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


# Telegram Schemas
class TelegramConfigBase(BaseModel):
    bot_token: str = Field(min_length=10)
    allowed_chat_ids: str = Field(default="[]")  # JSON array
    rate_limit: int = Field(default=10, ge=1, le=100)
    enabled: bool = Field(default=True)


class TelegramConfigUpdate(TelegramConfigBase):
    pass


class TelegramConfigResponse(BaseModel):
    id: int
    bot_token: str = "***"  # Masked for security
    allowed_chat_ids: str
    rate_limit: int
    enabled: bool
    
    class Config:
        from_attributes = True


class TelegramTestMessage(BaseModel):
    chat_id: str = Field(description="Telegram chat ID to send test message")
    message: str = Field(default="🤖 Test message from Telegram LLM Bot!", max_length=500)
