"""
Webhook support for Telegram bot (production mode)
"""
import logging
from typing import Optional
from fastapi import Request
from telegram import Update
from telegram.ext import Application

from .telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manages Telegram webhook for production deployment"""
    
    def __init__(self, bot_service: TelegramBotService):
        self.bot_service = bot_service
        self.webhook_url: Optional[str] = None
    
    async def set_webhook(self, webhook_url: str, secret_token: Optional[str] = None) -> bool:
        """
        Set webhook URL for Telegram bot
        
        Args:
            webhook_url: Full URL for webhook endpoint (e.g., https://example.com/webhook)
            secret_token: Optional secret token for webhook verification
        
        Returns:
            True if successful
        """
        try:
            if not self.bot_service.application:
                logger.error("Bot application not initialized")
                return False
            
            await self.bot_service.application.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token
            )
            self.webhook_url = webhook_url
            logger.info(f"Webhook set to: {webhook_url}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def delete_webhook(self) -> bool:
        """Delete webhook (switch back to polling)"""
        try:
            if not self.bot_service.application:
                return False
            
            await self.bot_service.application.bot.delete_webhook()
            self.webhook_url = None
            logger.info("Webhook deleted")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return False
    
    async def get_webhook_info(self) -> dict:
        """Get current webhook information"""
        try:
            if not self.bot_service.application:
                return {"error": "Bot not initialized"}
            
            info = await self.bot_service.application.bot.get_webhook_info()
            return {
                "url": info.url or None,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_date": info.last_error_date.isoformat() if info.last_error_date else None,
                "last_error_message": info.last_error_message,
                "max_connections": info.max_connections,
                "allowed_updates": info.allowed_updates
            }
        
        except Exception as e:
            logger.error(f"Failed to get webhook info: {e}")
            return {"error": str(e)}
    
    async def process_webhook_update(self, request: Request, secret_token: Optional[str] = None) -> dict:
        """
        Process incoming webhook update
        
        Args:
            request: FastAPI request object
            secret_token: Optional secret token for verification
        
        Returns:
            Processing result
        """
        try:
            # Verify secret token if provided
            if secret_token:
                provided_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                if provided_token != secret_token:
                    logger.warning("Invalid webhook secret token")
                    return {"error": "Invalid secret token"}
            
            # Parse update from request body
            body = await request.json()
            update = Update.de_json(body, self.bot_service.application.bot)
            
            if not update:
                return {"error": "Invalid update"}
            
            # Process update
            await self.bot_service.application.process_update(update)
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}", exc_info=True)
            return {"error": str(e)}
