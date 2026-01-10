from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HomeAssistantConfig
from ..schemas import TestResponse, HomeAssistantConfigResponse
from ..services import ha_client

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
            dry_run=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return HomeAssistantConfigResponse.model_validate(config)

@router.put("/config", response_model=HomeAssistantConfigResponse)
def update_ha_config(config_update: dict, db: Session = Depends(get_db)):
    """Update Home Assistant configuration"""
    config = db.query(HomeAssistantConfig).first()
    
    if not config:
        config = HomeAssistantConfig()
        db.add(config)
    
    # Update fields
    for key, value in config_update.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    return HomeAssistantConfigResponse.model_validate(config)

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
