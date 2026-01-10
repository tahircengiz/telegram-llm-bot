from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import TelegramConfig
from ..schemas import (
    TelegramConfigUpdate,
    TelegramConfigResponse,
    TelegramTestMessage,
    TestResponse
)

logger = logging.getLogger(__name__)

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
    
    # Mask token in response
    response_data = TelegramConfigResponse.model_validate(config)
    
    return response_data


@router.get("/me", response_model=TestResponse)
async def get_bot_info(db: Session = Depends(get_db)):
    """Get Telegram bot information"""
    config = db.query(TelegramConfig).first()
    
    if not config or not config.bot_token:
        return TestResponse(
            success=False,
            message="Telegram bot not configured. Please add bot token first."
        )
    
    try:
        from telegram import Bot
        
        bot = Bot(token=config.bot_token)
        bot_info = await bot.get_me()
        
        return TestResponse(
            success=True,
            message="Bot info retrieved successfully",
            details={
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot
            }
        )
        
    except Exception as e:
        return TestResponse(
            success=False,
            message=f"Failed to get bot info: {str(e)}"
        )


@router.put("/config", response_model=TelegramConfigResponse)
async def update_telegram_config(config_update: TelegramConfigUpdate, db: Session = Depends(get_db)):
    """Update Telegram bot configuration"""
    from ..services import bot_manager
    
    config = db.query(TelegramConfig).first()
    
    if not config:
        config = TelegramConfig()
        db.add(config)
    
    # Store old enabled state to check if we need to restart
    was_enabled = config.enabled
    old_token = config.bot_token
    
    # Update fields
    config.bot_token = config_update.bot_token
    config.allowed_chat_ids = config_update.allowed_chat_ids
    config.rate_limit = config_update.rate_limit
    config.enabled = config_update.enabled
    
    db.commit()
    db.refresh(config)
    
    # Restart bot if config changed and bot is enabled
    if (was_enabled or config.enabled) and (old_token != config.bot_token or was_enabled != config.enabled):
        try:
            logger.info("Config changed, restarting bot via BotManager...")
            manager = bot_manager.get_bot_manager()
            await manager.restart_bot(db)
        except Exception as e:
            logger.error(f"Error restarting bot after config update: {e}", exc_info=True)
    
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
    
    if not config.enabled:
        return TestResponse(
            success=False,
            message="Telegram bot is disabled. Enable it in config first."
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
    """Start Telegram bot (webhook or polling)"""
    from ..services import bot_manager
    
    config = db.query(TelegramConfig).first()
    
    if not config or not config.bot_token:
        return TestResponse(
            success=False,
            message="Telegram bot not configured. Please add bot token first."
        )
    
    if not config.enabled:
        return TestResponse(
            success=False,
            message="Telegram bot is disabled. Enable it in config first."
        )
    
    try:
        # Restart bot with current config using BotManager
        manager = bot_manager.get_bot_manager()
        bot = await manager.restart_bot(db)
        
        if bot:
            return TestResponse(
                success=True,
                message="Telegram bot started successfully",
                details={
                    "enabled": bool(config.enabled),
                    "rate_limit": int(config.rate_limit),
                    "running": manager.is_running()
                }
            )
        else:
            return TestResponse(
                success=False,
                message="Failed to start Telegram bot"
            )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error starting bot: {e}", exc_info=True)
        return TestResponse(
            success=False,
            message=f"Error starting Telegram bot: {str(e)}"
        )
