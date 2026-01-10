from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
import logging
from typing import Optional, Dict, Any
import re

from ..database import get_db, SessionLocal
from ..models import TelegramConfig, ConversationLog, LLMProvider, HomeAssistantConfig
from .llm_provider import LLMProviderFactory
from .ha_client import HomeAssistantClient
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import retry_async

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Telegram Bot Service"""
    
    def __init__(self, config: TelegramConfig):
        # Store config reference
        self.config = config
        
        # Extract actual values from database model
        # When config is a database model, access attributes directly
        try:
            self.bot_token = str(config.bot_token) if config.bot_token else ""
            self.allowed_chat_ids = self._parse_chat_ids(str(config.allowed_chat_ids) if config.allowed_chat_ids else "[]")
            self.enabled = bool(config.enabled) if hasattr(config, 'enabled') else False
            self.rate_limit = int(config.rate_limit) if hasattr(config, 'rate_limit') else 10
        except Exception as e:
            logger.error(f"Error extracting config values: {e}")
            self.bot_token = ""
            self.allowed_chat_ids = []
            self.enabled = False
            self.rate_limit = 10
        
        self.application = None
        self.ha_client: Optional[HomeAssistantClient] = None
        self.rate_limiter = RateLimiter(max_requests=self.rate_limit, time_window=60)
    
    def _parse_chat_ids(self, chat_ids_str: str) -> list:
        """Parse JSON chat IDs (supports regular IDs and group IDs)"""
        import json
        try:
            ids = json.loads(chat_ids_str)
            # Convert all IDs to strings for consistency
            return [str(i) for i in ids]
        except:
            return []
    
    def _init_ha_client(self, db: Session):
        """Initialize Home Assistant client"""
        ha_config = db.query(HomeAssistantConfig).first()
        if ha_config and ha_config.base_url:
            self.ha_client = HomeAssistantClient(ha_config.base_url, ha_config.api_token)
            logger.info(f"HA client initialized: {ha_config.base_url}")
        else:
            self.ha_client = None
    
    def _is_ha_command(self, message: str) -> bool:
        """Check if message is a Home Assistant command"""
        ha_commands = [
            r'/(\w+)\s+(on|off)',
            r'/(\w+)\s+set\s+(\d+\.?\d*)',
            r'(\w+)\s+(\w+)',
        ]
        return any(re.match(pattern, message, re.IGNORECASE) for pattern in ha_commands)
    
    async def _execute_ha_command(self, message: str) -> Dict[str, Any]:
        """Execute Home Assistant command"""
        if not self.ha_client:
            return {"success": False, "message": "Home Assistant not configured"}
        
        try:
            # Pattern matching for HA commands
            message = message.strip().lower()
            
            if "on" in message:
                # Extract entity ID: /light.turn_on on -> light
                parts = message.split()
                entity_id = parts[0].replace("/", "")
                return await self.ha_client.turn_on(entity_id)
            
            elif "off" in message:
                parts = message.split()
                entity_id = parts[0].replace("/", "")
                return await self.ha_client.turn_off(entity_id)
            
            elif "set" in message and "temperature" in message:
                # Extract entity and temperature: /thermostat set 22
                parts = message.split()
                entity_id = parts[0].replace("/", "")
                temp = float(parts[-1])
                return await self.ha_client.set_temperature(entity_id, temp)
            
            elif message.startswith("/"):
                # Direct service call: /entity_name.service
                entity_id = message[1:].split(".")[0]
                service = message[1:].split(".")[1] if "." in message[1:] else "turn_on"
                return await self.ha_client.call_service(entity_id.split(".")[0], service)
            
            else:
                return {"success": False, "message": "Unknown HA command format"}
                
        except Exception as e:
            logger.error(f"HA command error: {e}")
            return {"success": False, "message": str(e)}
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages with rate limiting and error handling"""
        
        # Get effective chat
        if not update.effective_chat:
            logger.warning("No effective_chat in update")
            return
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        logger.info(f"Received message from chat_id: {chat_id}")
        
        # Check if chat_id is allowed
        if chat_id not in self.allowed_chat_ids:
            logger.warning(f"Unauthorized chat ID: {chat_id}")
            try:
                await chat.send_message("❌ Bu bot sizin için yetkilendirilmemiş.")
            except Exception as e:
                logger.error(f"Failed to send unauthorized message: {e}")
            return
        
        # Rate limiting check
        if not self.rate_limiter.is_allowed(chat_id):
            remaining = self.rate_limiter.get_remaining(chat_id)
            logger.warning(f"Rate limit exceeded for chat {chat_id}")
            try:
                await chat.send_message(
                    f"⏳ Çok fazla mesaj gönderdiniz. Lütfen {remaining} saniye bekleyin."
                )
            except Exception as e:
                logger.error(f"Failed to send rate limit message: {e}")
            return
        
        # Get user message
        user_message = update.message.text if update.message else ""
        if not user_message:
            logger.info("No message text, skipping")
            return
        
        logger.info(f"User message: {user_message}")
        
        # Get LLM provider
        db = SessionLocal()
        try:
            # Initialize HA client
            self._init_ha_client(db)
            
            provider = LLMProviderFactory.get_active_provider(db)
            
            if not provider:
                await chat.send_message("❌ No LLM provider configured")
                return
            
            # Enhanced system prompt with HA integration
            system_prompt = """
Sen bir akıllı ev asistanısın. Kullanıcının mesajını anla ve aşağıdakilere göre cevap ver:

**Önemli:** Eğer kullanıcının mesajında Home Assistant cihaz kontrolü varsa:
1. İlgili entity'leri belirle (örn: light.salon, light.mutfak, switch.klima)
2. Hangi işlem yapılacak belirle (on/off/set_temperature)
3. Cevabın sonuna HA komutlarını JSON formatında ekle:

Cevap formatı:
[Normal LLM cevabı]

HA_COMMAND: {"entities": ["entity1", "entity2"], "action": "on/off", "temperature": 22}

Örnekler:
- "Salon ışıklarını aç" → HA_COMMAND: {"entities": ["light.salon"], "action": "on"}
- "Mutfak ışığını kapat" → HA_COMMAND: {"entities": ["light.mutfak"], "action": "off"}
- "Odayı 22 dereceye ayarla" → HA_COMMAND: {"entities": ["climate.oda"], "action": "set_temperature", "temperature": 22}
- "Bilmediğim bir soru" → Sadece cevap ver, HA_COMMAND ekleme
            """
            
            # Generate response with HA integration (with retry)
            try:
                async def generate_with_retry():
                    return await provider.generate(user_message, system_prompt)
                
                bot_response = await retry_async(
                    generate_with_retry,
                    max_retries=3,
                    delay=1.0,
                    backoff=2.0,
                    exceptions=(Exception,),
                    on_retry=lambda attempt, exc: logger.warning(
                        f"LLM generation retry {attempt}: {str(exc)}"
                    )
                )
                logger.info(f"LLM response: {bot_response}")
                
                # Check if HA command is in response
                ha_command = None
                if "HA_COMMAND:" in bot_response:
                    # Extract HA command
                    match = re.search(r'HA_COMMAND:\s*(\{.*?\})', bot_response)
                    if match:
                        try:
                            import json
                            ha_command = json.loads(match.group(1))
                            # Remove HA_COMMAND from response
                            bot_response = bot_response.split("HA_COMMAND:")[0].strip()
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse HA command")
                
                # Execute HA command if present
                if ha_command and self.ha_client:
                    try:
                        entities = ha_command.get("entities", [])
                        action = ha_command.get("action")
                        
                        for entity_id in entities:
                            if action == "on":
                                await self.ha_client.turn_on(entity_id)
                            elif action == "off":
                                await self.ha_client.turn_off(entity_id)
                            elif action == "set_temperature" and "temperature" in ha_command:
                                await self.ha_client.set_temperature(entity_id, ha_command["temperature"])
                        
                        bot_response += "\n\n✅ Akıllı ev komutu çalıştırıldı."
                    except Exception as e:
                        logger.error(f"HA command error: {e}")
                        bot_response += f"\n\n⚠️ Akıllı ev komutu başarısız: {str(e)}"
                
                # Send response (with retry)
                async def send_with_retry():
                    await chat.send_message(bot_response)
                
                await retry_async(
                    send_with_retry,
                    max_retries=2,
                    delay=0.5,
                    exceptions=(Exception,)
                )
                logger.info(f"Sent response to chat {chat_id}")
                
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
                logger.error(f"LLM generation error: {e}", exc_info=True)
                try:
                    error_msg = "❌ Üzgünüm, bir hata oluştu. Lütfen daha sonra tekrar deneyin."
                    if logger.isEnabledFor(logging.DEBUG):
                        error_msg += f"\n\nHata: {str(e)}"
                    await chat.send_message(error_msg)
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
        
        finally:
            db.close()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        help_text = """
👋 Merhaba! Ben akıllı ev asistanınızım.

📝 Kullanabileceğiniz komutlar:

**LLM Chat:**
• Herhangi bir soru sorun, cevap vereceğim
• Doğal dil komutlarınızı anlayabilirim

**Home Assistant Komutları:**
• "Salon ışıklarını aç" - LLM entity'leri bulur ve açar
• "Yatak odasını kapat" - LLM entity'leri bulur ve kapatır
• "Odayı 22 dereceye ayarla" - LLM termostat'ı ayarlar

💡 Örnekler:
• "Bugün hava nasıl?" - LLM cevap verir
• "Salon ışıklarını aç" - HA komutu gönderir
• "Odayı 22 dereceye ayarla" - HA komutu gönderir

🔧 Ayarlar:
• Bot Admin Panel: http://192.168.7.62:8000
• LLM Provider: Ollama/OpenAI/Gemini seçebilirsiniz
• Chat ID'leri: Admin panel'den yönetebilirsiniz
        """
        await update.message.reply_text(help_text)
    
    def setup(self):
        """Setup bot application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        from telegram.ext import CommandHandler
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Telegram bot setup complete")
    
    async def start(self) -> bool:
        """Start bot with polling"""
        if not self.application:
            self.setup()
        
        try:
            await self.application.initialize()
            await self.application.updater.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot started and polling")
            return True
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self):
        """Stop bot"""
        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")


# Global bot instance
_bot_instance: Optional[TelegramBotService] = None


async def get_bot_instance() -> Optional[TelegramBotService]:
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


async def start_bot(token: str) -> bool:
    """Start Telegram bot with given token"""
    db = SessionLocal()
    try:
        config = db.query(TelegramConfig).first()
        if config and config.enabled and config.bot_token:
            global _bot_instance
            _bot_instance = TelegramBotService(config)
            success = await _bot_instance.start()
            logger.info("Telegram bot started via start_bot function")
            return success
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return False
    finally:
        db.close()


async def restart_bot():
    """Restart bot with new config"""
    global _bot_instance
    
    if _bot_instance:
        try:
            await _bot_instance.stop()
        except Exception as e:
            logger.error(f"Error stopping bot during restart: {e}")
        _bot_instance = None
    
    # Get fresh config and start new instance
    db = SessionLocal()
    try:
        config = db.query(TelegramConfig).first()
        if config and config.enabled and config.bot_token:
            _bot_instance = TelegramBotService(config)
            success = await _bot_instance.start()
            if success:
                logger.info("Bot restarted successfully")
            return _bot_instance
        else:
            logger.info("Bot not enabled or no token, skipping restart")
            return None
    finally:
        db.close()
