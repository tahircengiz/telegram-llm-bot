from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import LLMProvider, OllamaConfig, OpenAIConfig, GeminiConfig
from ..schemas import (
    LLMProviderResponse,
    OllamaConfigUpdate, OllamaConfigResponse,
    OpenAIConfigUpdate, OpenAIConfigResponse,
    GeminiConfigUpdate, GeminiConfigResponse,
    TestResponse
)

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/", response_model=List[LLMProviderResponse])
def list_providers(db: Session = Depends(get_db)):
    """List all LLM providers"""
    providers = db.query(LLMProvider).all()
    return providers


@router.get("/{provider_id}", response_model=LLMProviderResponse)
def get_provider(provider_id: int, db: Session = Depends(get_db)):
    """Get specific provider"""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("/{provider_id}/activate")
def activate_provider(provider_id: int, db: Session = Depends(get_db)):
    """Set provider as active (deactivate others)"""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Deactivate all others
    db.query(LLMProvider).update({LLMProvider.active: False})
    
    # Activate this one
    provider.active = True
    provider.enabled = True
    db.commit()
    
    return {"message": f"{provider.name} activated", "provider_id": provider_id}


# Ollama Endpoints
@router.get("/ollama/config", response_model=OllamaConfigResponse)
def get_ollama_config(db: Session = Depends(get_db)):
    """Get Ollama configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "ollama").first()
    if not provider:
        raise HTTPException(status_code=404, detail="Ollama provider not found")
    
    config = db.query(OllamaConfig).filter(OllamaConfig.provider_id == provider.id).first()
    if not config:
        # Create default config
        config = OllamaConfig(provider_id=provider.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.put("/ollama/config", response_model=OllamaConfigResponse)
def update_ollama_config(config_update: OllamaConfigUpdate, db: Session = Depends(get_db)):
    """Update Ollama configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "ollama").first()
    if not provider:
        raise HTTPException(status_code=404, detail="Ollama provider not found")
    
    config = db.query(OllamaConfig).filter(OllamaConfig.provider_id == provider.id).first()
    if not config:
        config = OllamaConfig(provider_id=provider.id)
        db.add(config)
    
    # Update fields
    for key, value in config_update.model_dump().items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.post("/ollama/test", response_model=TestResponse)
async def test_ollama(db: Session = Depends(get_db)):
    """Test Ollama connectivity"""
    config = db.query(OllamaConfig).first()
    if not config:
        return TestResponse(success=False, message="Ollama not configured")
    
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{config.base_url}/api/version", timeout=5.0)
            if response.status_code == 200:
                return TestResponse(
                    success=True,
                    message="Ollama connection successful",
                    details=response.json()
                )
            else:
                return TestResponse(
                    success=False,
                    message=f"Ollama returned status {response.status_code}"
                )
    except Exception as e:
        return TestResponse(success=False, message=f"Connection failed: {str(e)}")


# OpenAI Endpoints (similar structure)
@router.get("/openai/config", response_model=OpenAIConfigResponse)
def get_openai_config(db: Session = Depends(get_db)):
    """Get OpenAI configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "openai").first()
    if not provider:
        raise HTTPException(status_code=404, detail="OpenAI provider not found")
    
    config = db.query(OpenAIConfig).filter(OpenAIConfig.provider_id == provider.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="OpenAI not configured yet")
    
    return config


@router.put("/openai/config", response_model=OpenAIConfigResponse)
def update_openai_config(config_update: OpenAIConfigUpdate, db: Session = Depends(get_db)):
    """Update OpenAI configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "openai").first()
    if not provider:
        raise HTTPException(status_code=404, detail="OpenAI provider not found")
    
    config = db.query(OpenAIConfig).filter(OpenAIConfig.provider_id == provider.id).first()
    if not config:
        config = OpenAIConfig(provider_id=provider.id)
        db.add(config)
    
    # Update fields (encrypt API key here in production)
    for key, value in config_update.model_dump().items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    # Mask API key in response
    response_data = OpenAIConfigResponse.model_validate(config)
    return response_data


# Gemini Endpoints (similar structure)
@router.get("/gemini/config", response_model=GeminiConfigResponse)
def get_gemini_config(db: Session = Depends(get_db)):
    """Get Gemini configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "gemini").first()
    if not provider:
        raise HTTPException(status_code=404, detail="Gemini provider not found")
    
    config = db.query(GeminiConfig).filter(GeminiConfig.provider_id == provider.id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Gemini not configured yet")
    
    return config


@router.put("/gemini/config", response_model=GeminiConfigResponse)
def update_gemini_config(config_update: GeminiConfigUpdate, db: Session = Depends(get_db)):
    """Update Gemini configuration"""
    provider = db.query(LLMProvider).filter(LLMProvider.name == "gemini").first()
    if not provider:
        raise HTTPException(status_code=404, detail="Gemini provider not found")
    
    config = db.query(GeminiConfig).filter(GeminiConfig.provider_id == provider.id).first()
    if not config:
        config = GeminiConfig(provider_id=provider.id)
        db.add(config)
    
    # Update fields (encrypt API key here in production)
    for key, value in config_update.model_dump().items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    # Mask API key in response
    response_data = GeminiConfigResponse.model_validate(config)
    return response_data
