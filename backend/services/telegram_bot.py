from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
import logging

from ..database import get_db, SessionLocal
from ..models import TelegramConfig, ConversationLog
from .llm_provider import LLMProviderFactory

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Telegram Bot Service"""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.application = None
        self.allowed_chat_ids = self._parse_chat_ids(config.allowed_chat_ids)
    
    def _parse_chat_ids(self, chat_ids_str: str) -> list:
        """Parse JSON chat IDs"""
        import json
        try:
            return json.loads(chat_ids_str)
        except:
            return []
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        
        # Check if chat_id is allowed
        chat_id = str(update.effective_chat.id)
        if chat_id not in self.allowed_chat_ids:
            await update.message.reply_text("⛔ Unauthorized. Please contact admin.")
            return
        
        # Get user message
        user_message = update.message.text
        
        # Get LLM provider
        db = SessionLocal()
        try:
            provider = LLMProviderFactory.get_active_provider(db)
            
            if not provider:
                await update.message.reply_text("❌ No LLM provider configured")
                return
            
            # Generate response
            try:
                bot_response = await provider.generate(user_message)
                
                # Send response
                await update.message.reply_text(bot_response)
                
                # Log conversation
                log = ConversationLog(
                    chat_id=chat_id,
                    user_message=user_message,
                    bot_response=bot_response,
                    llm_provider=db.query(LLMProvider).filter(LLMProvider.active == True).first().name
                )
                db.add(log)
                db.commit()
                
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                await update.message.reply_text(f"❌ Error: {str(e)}")
        
        finally:
            db.close()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Merhaba! Ben akıllı ev asistanınızım.\n\n"
            "Bana istediğiniz soruyu sorabilir veya komut verebilirsiniz."
        )
    
    def setup(self):
        """Setup bot application"""
        self.application = Application.builder().token(self.config.bot_token).build()
        
        # Add handlers
        from telegram.ext import CommandHandler
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Telegram bot setup complete")
    
    async def start(self):
        """Start the bot"""
        if not self.application:
            self.setup()
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")


# Global bot instance
_bot_instance: TelegramBotService = None


async def get_bot_instance() -> TelegramBotService:
    """Get or create bot instance"""
    global _bot_instance
    
    if _bot_instance is None:
        db = SessionLocal()
        try:
            config = db.query(TelegramConfig).first()
            if config and config.enabled:
                _bot_instance = TelegramBotService(config)
                await _bot_instance.start()
        finally:
            db.close()
    
    return _bot_instance


async def restart_bot():
    """Restart bot with new config"""
    global _bot_instance
    
    if _bot_instance:
        await _bot_instance.stop()
        _bot_instance = None
    
    return await get_bot_instance()
