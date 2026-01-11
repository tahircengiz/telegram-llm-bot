from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import HomeAssistantConfig
from ..schemas import TestResponse, HomeAssistantConfigResponse, HomeAssistantConfigUpdate
from ..services import ha_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/homeassistant", tags=["homeassistant"])

@router.get("/config", response_model=HomeAssistantConfigResponse)
def get_ha_config(db: Session = Depends(get_db)):
    """Get Home Assistant configuration"""
    config = db.query(HomeAssistantConfig).first()
    
    if not config:
        # Create default config
        config = HomeAssistantConfig(
            base_url="",
            api_token="",
            dry_run_mode=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    # Convert to response format (dry_run_mode -> dry_run)
    response_data = {
        "id": config.id,
        "base_url": config.base_url,
        "api_token": "***",  # Masked
        "dry_run": config.dry_run_mode
    }
    
    return HomeAssistantConfigResponse(**response_data)

@router.put("/config", response_model=HomeAssistantConfigResponse)
def update_ha_config(config_update: HomeAssistantConfigUpdate, db: Session = Depends(get_db)):
    """Update Home Assistant configuration"""
    config = db.query(HomeAssistantConfig).first()
    
    if not config:
        config = HomeAssistantConfig()
        db.add(config)
    
    # Update fields (dry_run -> dry_run_mode)
    config.base_url = config_update.base_url
    config.api_token = config_update.api_token
    config.dry_run_mode = config_update.dry_run
    
    db.commit()
    db.refresh(config)
    
    # Convert to response format
    response_data = {
        "id": config.id,
        "base_url": config.base_url,
        "api_token": "***",  # Masked
        "dry_run": config.dry_run_mode
    }
    
    return HomeAssistantConfigResponse(**response_data)

@router.get("/test")
async def test_ha_connection(db: Session = Depends(get_db)):
    """Test Home Assistant connection"""
    config = db.query(HomeAssistantConfig).first()
    
    if not config or not config.base_url:
        return {
            "success": False,
            "message": "Home Assistant not configured. Please add base URL first."
        }
    
    try:
        client = ha_client.HomeAssistantClient(config.base_url, config.api_token)
        result = await client.test_connection()
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }
