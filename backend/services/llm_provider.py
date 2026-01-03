from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import LLMProvider, OllamaConfig, OpenAIConfig, GeminiConfig
from ..database import get_db


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test provider connectivity"""
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM Provider"""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
    
    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Ollama"""
        import httpx
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        else:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "stream": False,
                    "options": {
                        "num_predict": self.config.max_tokens
                    }
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config.base_url}/api/version",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Connection successful",
                        "details": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "message": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider"""
    
    def __init__(self, config: OpenAIConfig):
        self.config = config
    
    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using OpenAI"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.config.api_key)
        
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        else:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.config.api_key)
            
            # Simple test with minimal tokens
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            
            return {
                "success": True,
                "message": "Connection successful",
                "details": {
                    "model": self.config.model,
                    "response": response.choices[0].message.content
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""
    
    def __init__(self, config: GeminiConfig):
        self.config = config
    
    async def generate(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using Gemini"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.config.api_key)
        model = genai.GenerativeModel(self.config.model)
        
        # Combine context and prompt
        full_prompt = f"{context or self.config.system_prompt}\n\nUser: {prompt}"
        
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens
            )
        )
        
        return response.text
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Gemini connection"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)
            
            response = model.generate_content("Hi")
            
            return {
                "success": True,
                "message": "Connection successful",
                "details": {
                    "model": self.config.model,
                    "response": response.text
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }


class LLMProviderFactory:
    """Factory to get the active LLM provider"""
    
    @staticmethod
    def get_active_provider(db: Session) -> Optional[BaseLLMProvider]:
        """Get currently active LLM provider"""
        
        # Find active provider
        active = db.query(LLMProvider).filter(LLMProvider.active == True).first()
        
        if not active:
            return None
        
        # Load config and instantiate
        if active.name == "ollama":
            config = db.query(OllamaConfig).filter(OllamaConfig.provider_id == active.id).first()
            if config:
                return OllamaProvider(config)
        
        elif active.name == "openai":
            config = db.query(OpenAIConfig).filter(OpenAIConfig.provider_id == active.id).first()
            if config:
                return OpenAIProvider(config)
        
        elif active.name == "gemini":
            config = db.query(GeminiConfig).filter(GeminiConfig.provider_id == active.id).first()
            if config:
                return GeminiProvider(config)
        
        return None
