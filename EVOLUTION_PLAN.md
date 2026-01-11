# Evrensel Akıllı Ev Asistanı - Geliştirme Planı

## 🎯 Hedef
Sistemin her Home Assistant kurulumunda, her entity tipinde ve her service'te sorunsuz çalışması. LLM'in tam zekasını kullanarak:
1. Mesajı anlamak
2. Sistemde ne olduğunu bulmak (entity discovery)
3. Ne yapacağını anlamak
4. Doğru komutları bulup göndermek

## 🔍 Mevcut Sorunlar

### 1. Format Uyumsuzluğu
- LLM eski format kullanıyor: `{"entities": [...], "action": ""}`
- Yeni format: `{"type": "service/get_state", "domain": "...", "service": "...", "entity_id": "..."}`
- **Çözüm**: Backward compatibility + format validation

### 2. Entity Capability Bilgisi Yok
- `group.salon_ve_kucukoda_petekler` için `turn_on` çalışmıyor (400 hatası)
- Group entity'ler farklı service'ler kullanabilir
- **Çözüm**: Entity state ve capabilities discovery

### 3. State-Aware Command Eksikliği
- "Petekleri açık mı?" → LLM "on" action gönderiyor (yanlış!)
- "Sıcaklık kaç?" → LLM boş action gönderiyor
- **Çözüm**: Soru tespiti ve otomatik state okuma

### 4. Service Discovery Yok
- Hangi service'ler mevcut bilinmiyor
- Hangi parametreler gerekli bilinmiyor
- **Çözüm**: HA API'den service listesi çekme

## 📋 Geliştirme Planı

### Faz 1: Service & Entity Discovery (Temel Altyapı)

#### 1.1 Service Discovery
```python
# ha_client.py
async def get_services(self) -> Dict[str, List[Dict]]:
    """Get all available services from HA"""
    # GET /api/services
    # Returns: {"light": [{"service": "turn_on", "fields": {...}}, ...]}
```

**Kullanım:**
- LLM prompt'una mevcut service'leri ekle
- Entity'nin domain'ine göre uygun service'leri göster

#### 1.2 Entity State & Capabilities
```python
async def get_entity_info(self, entity_id: str) -> Dict:
    """Get entity state + supported features"""
    state = await self.get_states(entity_id)
    # Extract: domain, state, attributes, supported_features
    return {
        "entity_id": entity_id,
        "domain": entity_id.split(".")[0],
        "state": state["state"],
        "attributes": state["attributes"],
        "supported_features": state.get("attributes", {}).get("supported_features", 0)
    }
```

**Kullanım:**
- LLM'e entity'nin mevcut state'ini göster
- Hangi service'lerin çalışacağını belirle

### Faz 2: Akıllı Command Generation

#### 2.1 Enhanced LLM Prompt
```python
system_prompt = f"""
**Mevcut Entity'ler ve State'leri:**
{formatted_entity_list_with_states}

**Mevcut Service'ler:**
{formatted_service_list}

**Kurallar:**
1. Soru soruluyorsa (?, nedir, kaç, açık mı) → type: "get_state"
2. İşlem yapılacaksa → type: "service", doğru domain ve service kullan
3. Entity'nin mevcut state'ini kontrol et
4. Group entity'ler için group domain service'lerini kullan
"""
```

#### 2.2 Question Detection
```python
def is_question(self, message: str) -> bool:
    """Detect if message is a question"""
    question_words = ["kaç", "nedir", "ne", "açık mı", "kapalı mı", "var mı"]
    return any(word in message.lower() for word in question_words) or "?" in message
```

### Faz 3: Error Handling & Self-Correction

#### 3.1 Error Analysis
```python
async def handle_ha_error(self, error: Exception, ha_command: Dict) -> Dict:
    """Analyze error and suggest correction"""
    if "400" in str(error):
        # Bad request - wrong service or parameters
        # Try to get entity info and suggest correct service
        entity_info = await self.get_entity_info(ha_command["entity_id"])
        # Return corrected command or error message for LLM
```

#### 3.2 LLM Self-Correction
```python
# Hata olduğunda LLM'e geri dön:
correction_prompt = f"""
Önceki komut başarısız oldu: {error_message}
Entity bilgisi: {entity_info}
Lütfen düzeltilmiş komut üret:
HA_COMMAND: ...
"""
```

### Faz 4: State-Aware Commands

#### 4.1 Pre-Command State Check
```python
# Komut göndermeden önce:
if command_type == "service" and service in ["turn_on", "turn_off"]:
    current_state = await self.get_entity_state(entity_id)
    if service == "turn_on" and current_state == "on":
        # Zaten açık, kullanıcıya bilgi ver
        return "Zaten açık"
```

#### 4.2 Post-Command Verification
```python
# Komut gönderdikten sonra:
result = await self.call_service(...)
# State'i tekrar oku ve doğrula
new_state = await self.get_entity_state(entity_id)
if expected_state != new_state:
    # Hata var, LLM'e bildir
```

## 🏗️ Mimari Değişiklikler

### Yeni Dosyalar
1. `backend/services/ha_discovery.py` - Service ve entity discovery
2. `backend/services/command_validator.py` - Command validation ve correction
3. `backend/utils/question_detector.py` - Soru tespiti

### Güncellenecek Dosyalar
1. `backend/services/ha_client.py` - Service discovery ekle
2. `backend/services/telegram_bot.py` - Enhanced prompt ve error handling
3. `backend/services/entity_cache.py` - Entity state ve capabilities cache

## 📊 Veri Akışı

```
User Message
    ↓
Question Detection → Soru mu? → get_state
    ↓
Entity Discovery → Entity bul
    ↓
Entity Info → State, capabilities, available services
    ↓
LLM Prompt (Enhanced) → Context-rich prompt
    ↓
LLM Response → HA_COMMAND
    ↓
Command Validation → Entity ve service kontrolü
    ↓
Execute → call_service veya get_state
    ↓
Error? → Error Analysis → LLM Correction → Retry
    ↓
Success → Response to user
```

## 🎯 Öncelik Sırası

### Yüksek Öncelik (Hemen)
1. ✅ Service discovery API ekle
2. ✅ Entity state bilgisini prompt'a ekle
3. ✅ Soru tespiti ve otomatik get_state
4. ✅ Error handling iyileştir

### Orta Öncelik (Sonraki Sprint)
5. ⏳ LLM self-correction (hata olduğunda düzeltme)
6. ⏳ Pre-command state check
7. ⏳ Post-command verification

### Düşük Öncelik (Gelecek)
8. ⏳ Entity capability learning (hangi service'ler çalışıyor öğren)
9. ⏳ Command history ve pattern learning
10. ⏳ Multi-entity batch operations

## 🧪 Test Senaryoları

1. **Soru Soruları:**
   - "Salon sıcaklığı kaç?" → get_state
   - "Petekler açık mı?" → get_state (yanlış: turn_on değil!)

2. **Group Entity:**
   - "Salon peteklerini aç" → group.turn_on (değil light.turn_on)

3. **Hata Düzeltme:**
   - 400 hatası → Entity info al → Doğru service bul → Retry

4. **State Awareness:**
   - "Işıkları aç" (zaten açık) → "Zaten açık" mesajı

## 📝 Notlar

- Home Assistant API: `/api/services` endpoint'i tüm service'leri döner
- Entity state: `/api/states/{entity_id}` endpoint'i state + attributes döner
- Group entities: `group` domain'i farklı service'ler kullanabilir
- Backward compatibility: Eski format desteği devam etmeli
