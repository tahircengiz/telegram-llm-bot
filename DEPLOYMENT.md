# Telegram LLM Bot - Deployment Guide

## 🚀 Production Deployment (Proxmox Server)

### Sunucu Bilgileri

- **Sunucu:** 192.168.7.222 (Proxmox)
- **Application URL:** http://192.168.7.62:8000
- **Deployment Method:** Docker + deploy.sh script
- **Repository:** https://github.com/tahircengiz/telegram-llm-bot

---

## 📋 Hızlı Deployment

### 1. Sunucuya Bağlan

```bash
ssh root@192.168.7.222
```

### 2. Deployment Script'ini Çalıştır

```bash
cd /root/telegram-llm-bot
./deploy.sh
```

Deployment script otomatik olarak:
- ✅ Mevcut versiyonu yedekler
- ✅ Git'ten son değişiklikleri çeker
- ✅ Yeni Docker image build eder
- ✅ Zero-downtime deployment yapar
- ✅ Health check yapar
- ✅ Başarısız olursa rollback yapar

### 3. Deployment Durumunu Kontrol Et

```bash
# Container durumu
docker ps | grep telegram-llm-bot

# Logs
docker logs -f telegram-llm-bot

# Health check
curl http://localhost:8000/api/health
```

---

## 🔧 Manuel Deployment

Eğer script kullanmak istemiyorsanız:

### 1. Git Pull

```bash
cd /root/telegram-llm-bot
git pull origin master
```

### 2. Docker Build

```bash
docker build -t telegram-llm-bot:latest .
```

### 3. Container'ı Durdur ve Yeniden Başlat

```bash
# Eski container'ı durdur
docker stop telegram-llm-bot
docker rm telegram-llm-bot

# Yeni container'ı başlat
docker run -d \
  --name telegram-llm-bot \
  -p 8000:8000 \
  -v /root/bot-data:/app/data \
  --restart unless-stopped \
  telegram-llm-bot:latest
```

---

## 📊 Deployment Script Detayları

`deploy.sh` script'i şu özelliklere sahip:

### Özellikler

1. **Backup:** Mevcut versiyonu yedekler
2. **Git Pull:** Son değişiklikleri çeker
3. **Build:** Yeni Docker image build eder
4. **Zero-Downtime:** Kesintisiz deployment
5. **Health Check:** Container sağlığını kontrol eder
6. **Rollback:** Başarısız olursa otomatik geri alır
7. **Logging:** Tüm işlemler `/root/deploy.log` dosyasına kaydedilir

### Script Çalışma Adımları

1. **Backup:** Mevcut image'ı `telegram-llm-bot:backup` olarak tagler
2. **Git Pull:** Master branch'ten son değişiklikleri çeker
3. **Build:** Yeni Docker image build eder (retry logic ile)
4. **Zero-Downtime Deploy:**
   - Yeni container'ı 8001 portunda başlatır
   - Health check yapar
   - Başarılıysa eski container'ı durdurur
   - Yeni container'ı 8000 portuna taşır
5. **Final Health Check:** 60 saniye boyunca kontrol eder
6. **Cleanup:** Eski image'ları temizler

### Rollback

Eğer deployment başarısız olursa:

```bash
# Manuel rollback
docker stop telegram-llm-bot
docker rm telegram-llm-bot
docker tag telegram-llm-bot:backup telegram-llm-bot:latest
docker run -d \
  --name telegram-llm-bot \
  -p 8000:8000 \
  -v /root/bot-data:/app/data \
  --restart unless-stopped \
  telegram-llm-bot:latest
```

---

## 🔍 Monitoring ve Logs

### Container Logs

```bash
# Real-time logs
docker logs -f telegram-llm-bot

# Son 100 satır
docker logs --tail 100 telegram-llm-bot

# Belirli bir tarihten itibaren
docker logs --since 2024-01-01T00:00:00 telegram-llm-bot
```

### Deployment Logs

```bash
# Deployment script logları
tail -f /root/deploy.log

# Son deployment
grep "SUCCESS" /root/deploy.log | tail -1
```

### Health Check

```bash
# API health check
curl http://192.168.7.62:8000/api/health

# Status endpoint
curl http://192.168.7.62:8000/api/status
```

### Container Durumu

```bash
# Container stats
docker stats telegram-llm-bot

# Container detayları
docker inspect telegram-llm-bot

# Port mapping
docker port telegram-llm-bot
```

---

## 🐛 Sorun Giderme

### Container Başlamıyor

```bash
# Logs kontrol
docker logs telegram-llm-bot

# Container durumu
docker ps -a | grep telegram-llm-bot

# Image kontrol
docker images | grep telegram-llm-bot
```

### Port Çakışması

```bash
# Port kullanımını kontrol et
netstat -tulpn | grep 8000

# Veya
ss -tulpn | grep 8000
```

### Database Sorunları

```bash
# Database dosyasını kontrol et
ls -lh /root/bot-data/bot.db

# Database backup
cp /root/bot-data/bot.db /root/bot-data/bot.db.backup

# Database permissions
chmod 644 /root/bot-data/bot.db
```

### Build Hataları

```bash
# Build cache temizle
docker builder prune -a

# Yeniden build
cd /root/telegram-llm-bot
docker build --no-cache -t telegram-llm-bot:latest .
```

---

## 🔄 Güncelleme Süreci

### Otomatik Güncelleme (Önerilen)

```bash
# Sunucuya bağlan
ssh root@192.168.7.222

# Deployment script'ini çalıştır
cd /root/telegram-llm-bot
./deploy.sh
```

### Manuel Güncelleme

1. **Kod değişikliklerini commit ve push et:**
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin master
   ```

2. **Sunucuda deployment yap:**
   ```bash
   ssh root@192.168.7.222
   cd /root/telegram-llm-bot
   ./deploy.sh
   ```

---

## 📝 Bot Yapılandırması

### İlk Kurulum

1. **Admin Panel'e Eriş:**
   - URL: http://192.168.7.62:8000
   - API Docs: http://192.168.7.62:8000/api/docs

2. **Telegram Bot Yapılandırması:**
   - Telegram Settings sayfasına git
   - Bot token ekle (BotFather'dan)
   - Chat ID ekle (JSON format: `["123456789"]`)
   - Rate limit ayarla (varsayılan: 10 mesaj/dakika)
   - "Enable Bot" switch'ini aç
   - "Save Configuration" butonuna tıkla

3. **LLM Provider Yapılandırması:**
   - Providers sayfasına git
   - Ollama/OpenAI/Gemini seç ve yapılandır
   - Aktif provider'ı seç

### Chat ID Nasıl Bulunur?

1. Bot'a Telegram'dan `/start` gönder
2. Tarayıcıda şu URL'yi aç:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. `chat.id` değerini bul ve admin panel'e ekle

---

## 🔐 Güvenlik

### Firewall

```bash
# Sadece gerekli portları aç
ufw allow 8000/tcp
ufw allow 22/tcp  # SSH
ufw enable
```

### SSL/HTTPS (Opsiyonel)

Nginx reverse proxy ile SSL eklenebilir:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Backup ve Restore

### Backup

```bash
# Database backup
cp /root/bot-data/bot.db /root/backups/bot.db.$(date +%Y%m%d_%H%M%S)

# Docker image backup
docker save telegram-llm-bot:latest | gzip > /root/backups/telegram-llm-bot-$(date +%Y%m%d).tar.gz
```

### Restore

```bash
# Database restore
cp /root/backups/bot.db.20240101_120000 /root/bot-data/bot.db

# Docker image restore
gunzip -c /root/backups/telegram-llm-bot-20240101.tar.gz | docker load
```

---

## 🆕 Yeni Özellikler (Son Güncelleme)

### İyileştirmeler

1. **Bot Instance Management:**
   - BotManager servisi ile dependency injection
   - Daha iyi lifecycle yönetimi
   - Otomatik restart mekanizması

2. **Error Handling:**
   - Retry mekanizması (exponential backoff)
   - Daha detaylı hata mesajları
   - Graceful error handling

3. **Rate Limiting:**
   - Token bucket algoritması
   - Chat ID bazlı rate limiting
   - Configurable rate limits

4. **Structured Logging:**
   - JSON format logging desteği
   - Daha iyi log yönetimi
   - Production-ready logging

5. **Webhook Desteği:**
   - Production için webhook modu
   - Webhook manager servisi
   - Secret token desteği

6. **Otomatik Başlatma:**
   - Startup event'te otomatik bot başlatma
   - Config değişikliklerinde otomatik restart

### Test

Test için `TESTING.md` dosyasına bakın:
```bash
cat TESTING.md
```

---

## 📚 Faydalı Komutlar

### Container Yönetimi

```bash
# Container'ı durdur
docker stop telegram-llm-bot

# Container'ı başlat
docker start telegram-llm-bot

# Container'ı yeniden başlat
docker restart telegram-llm-bot

# Container'ı sil (data korunur)
docker rm telegram-llm-bot
```

### Image Yönetimi

```bash
# Image listesi
docker images | grep telegram-llm-bot

# Eski image'ları temizle
docker image prune -f --filter "until=24h"

# Tüm eski image'ları temizle
docker image prune -a -f
```

### Volume Yönetimi

```bash
# Volume kontrol
docker volume ls

# Data dizini kontrol
ls -lh /root/bot-data/
```

---

## 🔗 Faydalı Linkler

- **Application:** http://192.168.7.62:8000
- **API Docs:** http://192.168.7.62:8000/api/docs
- **Health Check:** http://192.168.7.62:8000/api/health
- **GitHub Repository:** https://github.com/tahircengiz/telegram-llm-bot

---

## 📞 Destek

Sorun yaşarsanız:
1. Logs kontrol edin: `docker logs telegram-llm-bot`
2. Health check yapın: `curl http://192.168.7.62:8000/api/health`
3. Deployment loglarına bakın: `tail -f /root/deploy.log`
4. `TESTING.md` dosyasındaki troubleshooting bölümüne bakın
