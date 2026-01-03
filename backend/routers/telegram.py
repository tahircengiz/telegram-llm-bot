from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TelegramConfig
from ..schemas import (
    TelegramConfigUpdate,
    TelegramConfigResponse,
    TelegramTestMessage,
    TestResponse
)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/config", response_model=TelegramConfigResponse)
def get_telegram_config(db: Session = Depends(get_db)):
    """Get Telegram bot configuration"""
    config = db.query(TelegramConfig).first()
    
    if not config:
        # Create default config
        config = TelegramConfig(
            bot_token="",
            allowed_chat_ids="[]",
            rate_limit=10,
            enabled=False
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.put("/config", response_model=TelegramConfigResponse)
def update_telegram_config(config_update: TelegramConfigUpdate, db: Session = Depends(get_db)):
    """Update Telegram bot configuration"""
    config = db.query(TelegramConfig).first()
    
    if not config:
        config = TelegramConfig()
        db.add(config)
    
    # Update fields
    for key, value in config_update.model_dump().items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    
    # Mask token in response
    response_data = TelegramConfigResponse.model_validate(config)
    return response_data


@router.post("/test", response_model=TestResponse)
async def test_telegram(test_message: TelegramTestMessage, db: Session = Depends(get_db)):
    """Send a test message via Telegram bot"""
    config = db.query(TelegramConfig).first()
    
    if not config or not config.bot_token:
        return TestResponse(
            success=False,
            message="Telegram bot not configured. Please add bot token first."
        )
    
    try:
        from telegram import Bot
        
        bot = Bot(token=config.bot_token)
        
        # Send test message
        await bot.send_message(
            chat_id=test_message.chat_id,
            text=test_message.message
        )
        
        return TestResponse(
            success=True,
            message=f"Test message sent successfully to chat {test_message.chat_id}",
            details={
                "chat_id": test_message.chat_id,
                "message": test_message.message
            }
        )
        
    except Exception as e:
        return TestResponse(
            success=False,
            message=f"Failed to send test message: {str(e)}"
        )


@router.post("/start", response_model=TestResponse)
async def start_telegram_bot(db: Session = Depends(get_db)):
    """Start the Telegram bot (webhook or polling)"""
    config = db.query(TelegramConfig).first()
    
    if not config or not config.bot_token:
        return TestResponse(
            success=False,
            message="Telegram bot not configured"
        )
    
    if not config.enabled:
        return TestResponse(
            success=False,
            message="Telegram bot is disabled. Enable it in config first."
        )
    
    # TODO: Implement bot start logic
    # This would typically start polling or set up webhook
    
    return TestResponse(
        success=True,
        message="Telegram bot start feature coming soon. Configure bot token and chat IDs first.",
        details={
            "enabled": config.enabled,
            "rate_limit": config.rate_limit
        }
    )


@router.post("/stop", response_model=TestResponse)
async def stop_telegram_bot(db: Session = Depends(get_db)):
    """Stop the Telegram bot"""
    
    # TODO: Implement bot stop logic
    
    return TestResponse(
        success=True,
        message="Telegram bot stop feature coming soon"
    )


@router.get("/me", response_model=TestResponse)
async def get_bot_info(db: Session = Depends(get_db)):
    """Get bot information (username, name, etc.)"""
    config = db.query(TelegramConfig).first()
    
    if not config or not config.bot_token:
        return TestResponse(
            success=False,
            message="Telegram bot not configured"
        )
    
    try:
        from telegram import Bot
        
        bot = Bot(token=config.bot_token)
        me = await bot.get_me()
        
        return TestResponse(
            success=True,
            message="Bot info retrieved successfully",
            details={
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "is_bot": me.is_bot
            }
        )
        
    except Exception as e:
        return TestResponse(
            success=False,
            message=f"Failed to get bot info: {str(e)}"
        )
