from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import Session
import logging
from typing import Optional, Dict, Any, Tuple
import re

from ..database import get_db, SessionLocal
from ..models import TelegramConfig, ConversationLog, LLMProvider, HomeAssistantConfig
from .llm_provider import LLMProviderFactory
from .ha_client import HomeAssistantClient
from .entity_cache import get_entity_cache
from ..utils.rate_limiter import RateLimiter
from ..utils.retry import retry_async
from ..utils.question_detector import QuestionDetector

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
        self.ha_dry_run: bool = False
        self.rate_limiter = RateLimiter(max_requests=self.rate_limit, time_window=60)
        self.entity_cache = get_entity_cache()
        
        # Action to service mapping for generic service calls
        # Maps user-friendly actions to HA service names
        self.action_to_service = {
            "on": "turn_on",
            "off": "turn_off",
            "set_temperature": "set_temperature",
            "set_brightness": "turn_on",  # brightness is a parameter
            "set_color": "turn_on",  # color is a parameter
            "toggle": "toggle",
            "open": "open_cover",
            "close": "close_cover",
            "stop": "stop_cover",
            "lock": "lock",
            "unlock": "unlock",
        }
    
    def _parse_chat_ids(self, chat_ids_str: str) -> list:
        """Parse JSON chat IDs (supports regular IDs and group IDs)"""
        import json
        try:
            ids = json.loads(chat_ids_str)
            # Convert all IDs to strings for consistency (including negative group IDs)
            return [str(i) for i in ids]
        except:
            return []
    
    def _init_ha_client(self, db: Session):
        """Initialize Home Assistant client"""
        ha_config = db.query(HomeAssistantConfig).first()
        if ha_config and ha_config.base_url:
            self.ha_client = HomeAssistantClient(ha_config.base_url, ha_config.api_token)
            self.ha_dry_run = getattr(ha_config, 'dry_run_mode', False)
            logger.info(f"HA client initialized: {ha_config.base_url}, dry_run: {self.ha_dry_run}")
        else:
            self.ha_client = None
            self.ha_dry_run = False
            logger.warning("HA client not initialized - no config or base_url")
    
    async def _refresh_entity_cache(self):
        """Refresh entity cache from Home Assistant"""
        if not self.ha_client:
            return
        
        try:
            entities = await self.ha_client.get_states()
            self.entity_cache.set(entities)
            logger.info(f"Refreshed entity cache: {len(entities)} entities")
        except Exception as e:
            logger.error(f"Failed to refresh entity cache: {e}")
    
    def _get_entity_list_for_prompt(self) -> str:
        """Get formatted entity list for LLM prompt"""
        # Try to get from cache first
        entity_list = self.entity_cache.get_entity_list_for_prompt()
        
        if entity_list == "Entity list not available":
            # Cache is empty, try to get from HA (async, but we'll trigger refresh)
            logger.warning("Entity cache empty, will refresh on next message")
            return "Entity list is being loaded..."
        
        return entity_list
    
    async def _get_enhanced_entity_list(self) -> str:
        """Get entity list with state information for enhanced prompt"""
        if not self.ha_client:
            return "Home Assistant not configured"
        
        try:
            cached = self.entity_cache.get()
            if not cached:
                return "Entity list is being loaded..."
            
            # Limit to first 100 entities to avoid prompt size issues
            entities = cached[:100]
            formatted = []
            
            for entity in entities:
                entity_id = entity.get("entity_id", "")
                attributes = entity.get("attributes", {})
                state = entity.get("state", "unknown")
                friendly_name = attributes.get("friendly_name", entity_id)
                domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
                
                # Add unit if available
                unit = attributes.get("unit_of_measurement", "")
                state_display = f"{state} {unit}".strip() if unit else state
                
                formatted.append(f"- {entity_id} ({friendly_name}): {state_display} [{domain}]")
            
            if len(cached) > 100:
                formatted.append(f"\n... ve {len(cached) - 100} entity daha")
            
            return "\n".join(formatted) if formatted else "No entities found"
        except Exception as e:
            logger.error(f"Error formatting entity list: {e}")
            return "Error loading entity list"
    
    async def _find_entity(self, query: str) -> Optional[str]:
        """Find entity ID by name/query (fuzzy matching)"""
        if not self.ha_client:
            return None
        
        try:
            # Get cached entities
            cached = self.entity_cache.get()
            if not cached:
                return None
            
            query_lower = query.lower().strip()
            
            # Exact match first
            for entity in cached:
                entity_id = entity.get("entity_id", "")
                if entity_id.lower() == query_lower:
                    return entity_id
            
            # Fuzzy match
            best_match = None
            best_score = 0
            
            for entity in cached:
                entity_id = entity.get("entity_id", "")
                attributes = entity.get("attributes", {})
                friendly_name = attributes.get("friendly_name", "").lower()
                
                # Check if query matches entity_id or friendly_name
                if query_lower in entity_id.lower() or query_lower in friendly_name:
                    # Score based on match quality
                    score = 0
                    if query_lower in entity_id.lower():
                        score += 2
                    if query_lower in friendly_name:
                        score += 3
                    if entity_id.lower().startswith(query_lower):
                        score += 1
                    
                    if score > best_score:
                        best_score = score
                        best_match = entity_id
            
            return best_match if best_match else None
            
        except Exception as e:
            logger.error(f"Error finding entity: {e}")
            return None
    
    async def _execute_ha_command_generic(self, ha_command: Dict[str, Any], bot_response: str, dry_run: bool = False) -> Tuple[str, int, list]:
        """
        Generic HA command executor - LLM decides the service, we just call it.
        Returns: (updated_bot_response, success_count, error_messages)
        """
        command_type = ha_command.get("type", "service")  # "service" or "get_state"
        entity_id = ha_command.get("entity_id")
        success_count = 0
        error_messages = []
        
        # Backward compatibility: support old format
        if "entities" in ha_command and not entity_id:
            entities = ha_command.get("entities", [])
            action = ha_command.get("action")
            if entities and action:
                # Convert old format to new format
                entity_id = entities[0]  # Take first entity
                if action == "get_state" or not action or action == "":
                    command_type = "get_state"
                else:
                    # Try to infer domain and service from action
                    domain = entity_id.split(".")[0] if "." in entity_id else "light"
                    service = self.action_to_service.get(action, action)
                    ha_command = {
                        "type": "service",
                        "domain": domain,
                        "service": service,
                        "entity_id": entity_id,
                        "data": ha_command.get("data", {})
                    }
                    if "temperature" in ha_command:
                        ha_command["data"]["temperature"] = ha_command["temperature"]
                    command_type = "service"
        
        if not entity_id:
            error_messages.append("Entity ID bulunamadı")
            return bot_response, success_count, error_messages
        
        try:
            if command_type == "get_state":
                # Read entity state
                states = await self.ha_client.get_states(entity_id)
                if states and len(states) > 0:
                    state = states[0]
                    state_value = state.get("state", "N/A")
                    attributes = state.get("attributes", {})
                    unit = attributes.get("unit_of_measurement", "")
                    friendly_name = attributes.get("friendly_name", entity_id)
                    
                    if unit:
                        value_str = f"{state_value} {unit}"
                    else:
                        value_str = str(state_value)
                    
                    # Update bot response with actual value
                    if "**" in bot_response or "derece" in bot_response.lower() or "°" in bot_response:
                        # Replace placeholder
                        bot_response = re.sub(r'\*\*[\d.]+\*\*', f"**{state_value}**", bot_response)
                        bot_response = re.sub(r'[\d.]+(?=\s*(derece|°|%))', state_value, bot_response)
                        if unit and unit not in bot_response:
                            bot_response = bot_response.replace(state_value, f"{state_value} {unit}")
                    else:
                        # Add value if not present
                        bot_response += f"\n\n📊 {friendly_name}: **{value_str}**"
                    
                    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Read state for {entity_id}: {value_str}")
                    success_count += 1
                else:
                    error_messages.append(f"{entity_id}: Değer okunamadı")
                    
            elif command_type == "service":
                # Generic service call
                domain = ha_command.get("domain")
                service = ha_command.get("service")
                data = ha_command.get("data", {})
                
                if not domain or not service:
                    error_messages.append(f"Domain veya service belirtilmemiş: domain={domain}, service={service}")
                else:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would call service: {domain}.{service} on {entity_id} with data: {data}")
                        bot_response += f"\n\n🔍 [DRY RUN] Komut çalıştırılacaktı: {domain}.{service} → {entity_id}"
                    else:
                        try:
                            result = await self.ha_client.call_service(domain, service, entity_id, data)
                            logger.info(f"Successfully called {domain}.{service} on {entity_id}: {result}")
                            success_count += 1
                        except Exception as e:
                            error_str = str(e)
                            logger.error(f"Service call failed: {error_str}")
                            
                            # Try to fix common errors
                            if "400" in error_str:
                                # Bad request - try to get entity info and suggest fix
                                try:
                                    entity_info = await self.ha_client.get_entity_info(entity_id)
                                    if entity_info:
                                        actual_domain = entity_info.get("domain")
                                        if actual_domain and actual_domain != domain:
                                            # Domain mismatch - try with correct domain
                                            logger.info(f"Domain mismatch detected: {domain} → {actual_domain}, retrying...")
                                            try:
                                                result = await self.ha_client.call_service(actual_domain, service, entity_id, data)
                                                logger.info(f"Successfully called {actual_domain}.{service} on {entity_id} after domain correction: {result}")
                                                success_count += 1
                                            except Exception as retry_e:
                                                error_messages.append(f"Domain düzeltmesi sonrası hata: {str(retry_e)}")
                                        else:
                                            # Check if it's a group entity - might need group service
                                            if actual_domain == "group":
                                                # Group entities might need group.turn_on instead of light.turn_on
                                                if service in ["turn_on", "turn_off"]:
                                                    logger.info(f"Group entity detected, using group.{service}")
                                                    try:
                                                        result = await self.ha_client.call_service("group", service, entity_id, data)
                                                        logger.info(f"Successfully called group.{service} on {entity_id}: {result}")
                                                        success_count += 1
                                                    except Exception as group_e:
                                                        error_messages.append(f"Group service hatası: {str(group_e)}")
                                                else:
                                                    error_messages.append(f"Service hatası (400): {error_str}. Entity: {entity_id}, Domain: {actual_domain}")
                                            else:
                                                error_messages.append(f"Service hatası (400): {error_str}. Entity: {entity_id}, Domain: {actual_domain}")
                                    else:
                                        error_messages.append(f"Service hatası: {error_str}")
                                except Exception as info_e:
                                    logger.error(f"Error getting entity info for error correction: {info_e}")
                                    error_messages.append(f"Service hatası: {error_str}")
                            else:
                                error_messages.append(f"Service hatası: {error_str}")
            else:
                error_messages.append(f"Bilinmeyen komut tipi: {command_type}")
                
        except Exception as e:
            logger.error(f"Error executing HA command: {e}", exc_info=True)
            error_messages.append(f"{entity_id}: {str(e)}")
        
        # Add result message
        if not dry_run:
            if success_count > 0 and not error_messages:
                bot_response += f"\n\n✅ {success_count} komut başarıyla çalıştırıldı."
            elif success_count > 0:
                bot_response += f"\n\n⚠️ {success_count} komut çalıştırıldı, bazı hatalar: {', '.join(error_messages)}"
            elif error_messages:
                bot_response += f"\n\n❌ Komut çalıştırılamadı: {', '.join(error_messages)}"
        
        return bot_response, success_count, error_messages
    
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
        
        logger.info(f"Received message from chat_id: {chat_id}, type: {chat.type}")
        
        # Check if chat_id is allowed
        if chat_id not in self.allowed_chat_ids:
            logger.warning(f"Unauthorized chat ID: {chat_id}")
            
            # In group chats, only respond if bot is mentioned
            if chat.type in ['group', 'supergroup']:
                if update.message and update.message.text:
                    bot_username = context.bot.username if context.bot else None
                    if bot_username and f"@{bot_username}" in update.message.text:
                        # Bot is mentioned, allow response
                        logger.info(f"Bot mentioned in group chat {chat_id}")
                    else:
                        # Not mentioned, ignore
                        return
                else:
                    return
            else:
                # Private chat - send unauthorized message
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
        
        # Remove bot mention if present (for group chats)
        if chat.type in ['group', 'supergroup']:
            bot_username = context.bot.username if context.bot else None
            if bot_username:
                # Remove @bot_username mentions
                user_message = re.sub(rf'@{bot_username}\s*', '', user_message, flags=re.IGNORECASE)
                user_message = user_message.strip()
        
        logger.info(f"User message: {user_message}")
        
        # Get LLM provider
        db = SessionLocal()
        try:
            # Initialize HA client (always refresh to get latest config)
            self._init_ha_client(db)
            
            # Refresh entity cache if needed
            if self.ha_client and not self.entity_cache.is_valid():
                await self._refresh_entity_cache()
            
            provider = LLMProviderFactory.get_active_provider(db)
            
            if not provider:
                await chat.send_message("❌ No LLM provider configured")
                return
            
            # Check if message is a question requiring state read
            is_state_query = QuestionDetector.requires_state_read(user_message)
            
            # Get entity list with state information
            entity_list = await self._get_enhanced_entity_list() if self.ha_client else "Home Assistant not configured"
            
            # Get available services
            services_info = ""
            if self.ha_client:
                try:
                    services = await self.ha_client.get_services()
                    if services:
                        # Format services for prompt (limit to common domains)
                        common_domains = ["light", "switch", "climate", "cover", "lock", "group", "fan", "media_player"]
                        services_list = []
                        for domain in common_domains:
                            if domain in services:
                                domain_services = [s.get("service", "") for s in services[domain] if isinstance(s, dict)]
                                if domain_services:
                                    services_list.append(f"{domain}: {', '.join(domain_services[:10])}")  # Limit to 10 services per domain
                        if services_list:
                            services_info = "\n".join(services_list)
                except Exception as e:
                    logger.warning(f"Failed to get services: {e}")
            
            # Enhanced system prompt with HA integration
            system_prompt = f"""
Sen bir akıllı ev asistanısın. Kullanıcının mesajını anla ve Home Assistant komutlarını doğru formatta üret.

**Mevcut Home Assistant Entity'leri ve Durumları:**
{entity_list}

**Mevcut Service'ler:**
{services_info if services_info else "Service listesi yükleniyor..."}

**ÖNEMLİ KURALLAR:**

1. **Soru Tespiti:**
   - Kullanıcı soru soruyorsa (?, kaç, nedir, açık mı, kapalı mı) → MUTLAKA type: "get_state" kullan
   - "Açık mı?", "Kaç derece?", "Nedir?" gibi sorular için service çağrısı YAPMA, sadece state oku

2. **Entity Seçimi:**
   - Entity ID'leri yukarıdaki listeden tam olarak kullan
   - Entity'nin mevcut state'ini kontrol et (yukarıdaki listede var)
   - Group entity'ler için group domain service'lerini kullan (örn: group.turn_on, group.turn_off)

3. **Service Seçimi:**
   - Her entity'nin domain'ini belirle (light, switch, climate, sensor, cover, lock, group, vb.)
   - Yukarıdaki service listesinden doğru service'i seç
   - Group entity'ler için group domain service'lerini kullan

4. **Format:**
   - İşlem yapılacaksa: {{"type": "service", "domain": "light", "service": "turn_on", "entity_id": "light.salon", "data": {{}}}}
   - State okunacaksa: {{"type": "get_state", "entity_id": "sensor.salon_sicaklik"}}

**Örnekler:**
- "Salon ışıklarını aç" → HA_COMMAND: {{"type": "service", "domain": "light", "service": "turn_on", "entity_id": "light.salon", "data": {{}}}}
- "Salon sıcaklığı kaç derece?" → HA_COMMAND: {{"type": "get_state", "entity_id": "sensor.salon_sicaklik"}}
- "Petekler açık mı?" → HA_COMMAND: {{"type": "get_state", "entity_id": "group.salon_ve_kucukoda_petekler"}}
- "Petekleri aç" → HA_COMMAND: {{"type": "service", "domain": "group", "service": "turn_on", "entity_id": "group.salon_ve_kucukoda_petekler", "data": {{}}}}
- "Odayı 22 dereceye ayarla" → HA_COMMAND: {{"type": "service", "domain": "climate", "service": "set_temperature", "entity_id": "climate.oda", "data": {{"temperature": 22}}}}

**Not:** Eğer entity bulunamazsa veya işlem Home Assistant ile ilgili değilse, sadece cevap ver, HA_COMMAND ekleme.
            """
            
            # If it's a state query, hint LLM to use get_state
            if is_state_query:
                system_prompt += "\n\n⚠️ BU MESAJ BİR SORU! Mutlaka type: \"get_state\" kullan, service çağrısı YAPMA!"
            
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
                    match = re.search(r'HA_COMMAND:\s*(\{.*?\})', bot_response, re.DOTALL)
                    if match:
                        try:
                            import json
                            ha_command = json.loads(match.group(1))
                            # Remove HA_COMMAND from response
                            bot_response = bot_response.split("HA_COMMAND:")[0].strip()
                            
                            # Validate and fix entity ID if present
                            if ha_command and "entity_id" in ha_command:
                                entity_id = ha_command["entity_id"]
                                if self.ha_client:
                                    matched = await self._find_entity(entity_id)
                                    if matched:
                                        ha_command["entity_id"] = matched
                                        logger.info(f"Validated entity: {entity_id} → {matched}")
                                    else:
                                        logger.warning(f"Entity not found: {entity_id}, using as-is")
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse HA command: {e}")
                        except Exception as e:
                            logger.error(f"Error validating entity: {e}")
                
                # Execute HA command if present
                if ha_command:
                    if not self.ha_client:
                        logger.warning("HA command found but HA client not initialized")
                        bot_response += "\n\n⚠️ Home Assistant yapılandırılmamış. Lütfen admin panel'den yapılandırın."
                    elif self.ha_dry_run:
                        # Dry run mode
                        bot_response, success_count, error_messages = await self._execute_ha_command_generic(ha_command, bot_response, dry_run=True)
                    else:
                        # Execute command
                        bot_response, success_count, error_messages = await self._execute_ha_command_generic(ha_command, bot_response, dry_run=False)
                        
                        # Add result message
                        if success_count > 0 and not error_messages:
                            bot_response += f"\n\n✅ {success_count} komut başarıyla çalıştırıldı."
                        elif success_count > 0:
                            bot_response += f"\n\n⚠️ {success_count} komut çalıştırıldı, bazı hatalar: {', '.join(error_messages)}"
                        elif error_messages:
                            bot_response += f"\n\n❌ Komut çalıştırılamadı: {', '.join(error_messages)}"
                        
                        if error_messages and success_count == 0:
                            logger.error(f"HA command execution failed: {', '.join(error_messages)}")
                            bot_response += f"\n\n⚠️ Akıllı ev komutu başarısız: {', '.join(error_messages)}"
                
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
        """Handle /start command (works in both private and group chats)"""
        if not update.effective_chat:
            return
        
        chat = update.effective_chat
        chat_id = str(chat.id)
        
        # Check if chat is allowed (for group chats)
        if chat_id not in self.allowed_chat_ids:
            logger.warning(f"Unauthorized chat ID for /start: {chat_id}")
            if chat.type in ['group', 'supergroup']:
                # In groups, only respond if bot is mentioned
                if update.message and update.message.text:
                    bot_username = context.bot.username if context.bot else None
                    if bot_username and f"@{bot_username}" not in update.message.text:
                        return  # Don't respond if not mentioned
            else:
                # Private chat - send unauthorized message
                try:
                    await chat.send_message("❌ Bu bot sizin için yetkilendirilmemiş.")
                except Exception as e:
                    logger.error(f"Failed to send unauthorized message: {e}")
                return
        
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
        
        try:
            await update.message.reply_text(help_text)
        except Exception as e:
            logger.error(f"Failed to send /start response: {e}")
    
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
