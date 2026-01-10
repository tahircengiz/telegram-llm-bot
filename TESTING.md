# Telegram Bot Test Rehberi

## 🧪 Yerel Test

### 1. Bağımlılıkları Yükle

```bash
cd telegram-llm-bot/backend
pip install -r requirements.txt
```

### 2. Uygulamayı Başlat

```bash
# Backend'i başlat
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Veya Docker ile
docker build -t telegram-llm-bot .
docker run -p 8000:8000 -v $(pwd)/data:/app/data telegram-llm-bot
```

### 3. Admin Panel'e Eriş

- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs

### 4. Telegram Bot Yapılandırması

1. **Bot Token Al:**
   - Telegram'da @BotFather'a git
   - `/newbot` komutu ile yeni bot oluştur
   - Token'ı kopyala

2. **Admin Panel'de Yapılandır:**
   - Telegram Settings sayfasına git
   - Bot Token'ı yapıştır
   - Chat ID'lerini ekle (JSON array formatında: `["123456789"]`)
   - Rate Limit ayarla (varsayılan: 10 mesaj/dakika)
   - "Enable Bot" switch'ini aç
   - "Save Configuration" butonuna tıkla

3. **Chat ID Nasıl Bulunur:**
   - Bot'a Telegram'dan `/start` gönder
   - Tarayıcıda şu URL'yi aç: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - `chat.id` değerini bul

### 5. Bot'u Test Et

#### Manuel Test:
1. Telegram'da bot'a mesaj gönder
2. Bot cevap vermeli
3. Admin panel'de conversation logs kontrol et

#### API Test:
```bash
# Health check
curl http://localhost:8000/api/health

# Bot config kontrol
curl http://localhost:8000/api/telegram/config

# Bot bilgilerini al
curl http://localhost:8000/api/telegram/me

# Test mesajı gönder
curl -X POST http://localhost:8000/api/telegram/test \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "YOUR_CHAT_ID", "message": "Test mesajı"}'
```

## 🚀 Production Deployment Test

### 1. Deployment Öncesi Kontroller

```bash
# Docker image build test
docker build -t telegram-llm-bot:test .

# Container çalıştırma testi
docker run -d \
  --name telegram-llm-bot-test \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  telegram-llm-bot:test

# Health check
curl http://localhost:8000/api/health

# Logs kontrol
docker logs telegram-llm-bot-test
```

### 2. Kubernetes Deployment Test

```bash
# Namespace oluştur
kubectl create namespace telegram-llm-bot

# ConfigMap ve Secrets (gerekirse)
kubectl apply -f k8s/

# Deployment kontrol
kubectl get pods -n telegram-llm-bot

# Logs
kubectl logs -f deployment/telegram-llm-bot -n telegram-llm-bot

# Service kontrol
kubectl get svc -n telegram-llm-bot
```

### 3. ArgoCD Deployment Test

```bash
# ArgoCD app durumu
argocd app get telegram-llm-bot

# Sync durumu
argocd app sync telegram-llm-bot

# Logs
argocd app logs telegram-llm-bot --follow
```

## ✅ Test Checklist

### Fonksiyonel Testler

- [ ] Bot token kaydedilebiliyor
- [ ] Bot enable/disable çalışıyor
- [ ] Chat ID'ler doğru parse ediliyor
- [ ] Rate limiting çalışıyor
- [ ] Bot mesajları alıyor ve cevap veriyor
- [ ] LLM provider entegrasyonu çalışıyor
- [ ] Home Assistant komutları çalışıyor (eğer yapılandırıldıysa)
- [ ] Conversation logs kaydediliyor

### Performans Testleri

- [ ] Rate limit aşıldığında uyarı veriyor
- [ ] Retry mekanizması çalışıyor
- [ ] Error handling düzgün çalışıyor
- [ ] Bot restart çalışıyor

### Deployment Testleri

- [ ] Docker image build ediliyor
- [ ] Container sağlıklı başlıyor
- [ ] Health check endpoint çalışıyor
- [ ] Database migration çalışıyor
- [ ] Frontend serve ediliyor
- [ ] Kubernetes deployment başarılı
- [ ] ArgoCD sync çalışıyor

## 🐛 Sorun Giderme

### Bot Başlamıyor

1. **Logs kontrol et:**
   ```bash
   docker logs telegram-llm-bot
   # veya
   kubectl logs -f deployment/telegram-llm-bot -n telegram-llm-bot
   ```

2. **Config kontrol:**
   - Bot token doğru mu?
   - Bot enabled mi?
   - Chat ID'ler doğru format mı?

3. **Database kontrol:**
   ```bash
   # SQLite database kontrol
   sqlite3 data/bot.db "SELECT * FROM telegram_config;"
   ```

### Bot Mesaj Almıyor

1. **Chat ID kontrol:**
   - Chat ID doğru mu?
   - Allowed chat IDs listesinde var mı?

2. **Bot durumu:**
   ```bash
   curl http://localhost:8000/api/telegram/me
   ```

3. **Rate limit:**
   - Rate limit aşılmış olabilir
   - 1 dakika bekle ve tekrar dene

### LLM Provider Çalışmıyor

1. **Provider aktif mi:**
   ```bash
   curl http://localhost:8000/api/providers
   ```

2. **Ollama bağlantısı:**
   - Ollama servisi çalışıyor mu?
   - Base URL doğru mu?

## 📊 Monitoring

### Logs

```bash
# Docker
docker logs -f telegram-llm-bot

# Kubernetes
kubectl logs -f deployment/telegram-llm-bot -n telegram-llm-bot

# ArgoCD
argocd app logs telegram-llm-bot --follow
```

### Metrics

- Health endpoint: `/api/health`
- Status endpoint: `/api/status`
- Bot info: `/api/telegram/me`

## 🔗 Faydalı Linkler

- **Admin Panel:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/api/health
