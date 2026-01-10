"""
Bot Manager Service - Manages Telegram bot lifecycle with dependency injection
"""
from typing import Optional
import logging
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import TelegramConfig
from .telegram_bot import TelegramBotService

logger = logging.getLogger(__name__)


class BotManager:
    """Manages Telegram bot instance lifecycle"""
    
    def __init__(self):
        self._bot_instance: Optional[TelegramBotService] = None
        self._is_running: bool = False
    
    async def get_bot(self, db: Optional[Session] = None) -> Optional[TelegramBotService]:
        """
        Get or create bot instance
        
        Args:
            db: Optional database session (creates new if not provided)
        
        Returns:
            TelegramBotService instance or None if not configured
        """
        if self._bot_instance and self._is_running:
            return self._bot_instance
        
        # Use provided session or create new
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True
        
        try:
            config = db.query(TelegramConfig).first()
            
            if not config or not config.enabled or not config.bot_token:
                logger.info("Bot not configured or disabled")
                return None
            
            # Create new instance if needed
            if not self._bot_instance:
                self._bot_instance = TelegramBotService(config)
            
            # Start if not running
            if not self._is_running:
                success = await self._bot_instance.start()
                if success:
                    self._is_running = True
                    logger.info("Bot started successfully via BotManager")
                else:
                    logger.error("Failed to start bot")
                    self._bot_instance = None
                    return None
            
            return self._bot_instance
        
        finally:
            if should_close:
                db.close()
    
    async def restart_bot(self, db: Optional[Session] = None) -> Optional[TelegramBotService]:
        """
        Restart bot with fresh config
        
        Args:
            db: Optional database session
        
        Returns:
            TelegramBotService instance or None
        """
        logger.info("Restarting bot via BotManager...")
        
        # Stop current instance
        await self.stop_bot()
        
        # Get fresh instance
        return await self.get_bot(db)
    
    async def stop_bot(self):
        """Stop bot instance"""
        if self._bot_instance and self._is_running:
            try:
                await self._bot_instance.stop()
                logger.info("Bot stopped via BotManager")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
            finally:
                self._is_running = False
                # Keep instance for potential restart
    
    def is_running(self) -> bool:
        """Check if bot is currently running"""
        return self._is_running
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_bot()
        self._bot_instance = None


# Global bot manager instance
_bot_manager: Optional[BotManager] = None


def get_bot_manager() -> BotManager:
    """Get global bot manager instance"""
    global _bot_manager
    if _bot_manager is None:
        _bot_manager = BotManager()
    return _bot_manager
