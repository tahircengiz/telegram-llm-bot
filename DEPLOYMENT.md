# Telegram LLM Bot - Deployment Guide

## 🚀 Production Deployment (LXC Container)

### Sunucu Bilgileri

- **Sunucu:** 192.168.7.62 (LXC Container on Proxmox)
- **SSH User:** root
- **SSH Key:** ~/.ssh/id_ed25519
- **Application URL:** http://192.168.7.62:8000
- **Deployment Method:** Docker + deploy.sh script
- **Repository:** https://github.com/tahircengiz/telegram-llm-bot
- **Branch:** master

### Bot Bilgileri

- **Bot Token:** 8598475911:AAE6koTqfhoQanydNh7lL5aAd4CHxMcQAY
- **Chat ID:** -1003541895181
- **Database:** /root/bot-data (SQLite)

---

## 📋 Hızlı Deployment (GitHub'dan)

### Yerel Makineden Deployment

En kolay yöntem: `deploy_from_github.sh` script'ini kullanın:

```bash
cd telegram-llm-bot
./deploy_from_github.sh
```

Bu script otomatik olarak:
- ✅ SSH bağlantısını test eder
- ✅ Sunucuya bağlanır
- ✅ GitHub'dan güncel kodu çeker
- ✅ Deployment script'ini çalıştırır
- ✅ Health check yapar

### Manuel Deployment (Sunucuya Bağlanarak)

```bash
# 1. Sunucuya bağlan
ssh -i ~/.ssh/id_ed25519 root@192.168.7.62

# 2. Proje dizinine git (veya clone et)
cd /root/telegram-llm-bot

# Eğer dizin yoksa:
# git clone https://github.com/tahircengiz/telegram-llm-bot.git /root/telegram-llm-bot
# cd /root/telegram-llm-bot

# 3. Son değişiklikleri çek
git fetch origin master
git reset --hard origin/master
git clean -fd

# 4. Deployment script'ini çalıştır
./deploy.sh
```

---

## 🔧 Deployment Script Detayları

### `deploy.sh` (Sunucuda Çalışan)

Bu script sunucuda çalışır ve şunları yapar:

1. **Backup:** Mevcut Docker image'ı yedekler
2. **Git Pull:** GitHub'dan son değişiklikleri çeker
3. **Build:** Yeni Docker image build eder
4. **Zero-Downtime Deploy:** Kesintisiz deployment
5. **Health Check:** Container sağlığını kontrol eder
6. **Rollback:** Başarısız olursa otomatik geri alır

### `deploy_from_github.sh` (Yerel Makineden Çalışan)

Bu script yerel makinenizden çalışır ve:

1. SSH bağlantısını test eder
2. Sunucuya bağlanır
3. GitHub'dan güncel kodu çeker
4. `deploy.sh` script'ini çalıştırır
5. Deployment durumunu kontrol eder

---

## 📊 Deployment Adımları

### 1. Backup
- Mevcut image `telegram-llm-bot:backup` olarak taglenir
- Timestamp'li backup da oluşturulur

### 2. Git Pull
- GitHub'dan `master` branch çekilir
- `git reset --hard origin/master` ile güncel versiyona geçilir
- Untracked dosyalar temizlenir

### 3. Build
- Docker image build edilir
- Retry logic ile 3 deneme hakkı var
- Build logları `/root/deploy.log` dosyasına yazılır

### 4. Zero-Downtime Deploy
- Yeni container 8001 portunda başlatılır
- Health check yapılır
- Başarılıysa eski container durdurulur
- Yeni container 8000 portuna taşınır

### 5. Health Check
- 60 saniye boyunca health check yapılır
- `/api/health` endpoint'i kontrol edilir

### 6. Cleanup
- 24 saatten eski image'lar temizlenir

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

# Bot config
curl http://192.168.7.62:8000/api/telegram/config
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
# veya
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

### Git Pull Sorunları

```bash
# Git durumunu kontrol et
cd /root/telegram-llm-bot
git status

# Remote'u kontrol et
git remote -v

# Manuel pull
git fetch origin master
git reset --hard origin/master
```

---

## 🔄 Güncelleme Süreci

### Otomatik Güncelleme (Önerilen)

Yerel makinenizden:

```bash
cd telegram-llm-bot
./deploy_from_github.sh
```

### Manuel Güncelleme

1. **Kod değişikliklerini commit ve push et:**
   ```bash
   git add .
   git commit -m "feat: your changes"
   git push origin master
   ```

2. **Deployment yap:**
   ```bash
   ./deploy_from_github.sh
   ```

   Veya sunucuda:
   ```bash
   ssh -i ~/.ssh/id_ed25519 root@192.168.7.62
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
   - Bot token: `8598475911:AAE6koTqfhoQanydNh7lL5aAd4CHxMcQAY`
   - Chat ID: `-1003541895181` (JSON format: `["-1003541895181"]`)
   - Rate limit ayarla (varsayılan: 10 mesaj/dakika)
   - "Enable Bot" switch'ini aç
   - "Save Configuration" butonuna tıkla

3. **LLM Provider Yapılandırması:**
   - Providers sayfasına git
   - Ollama/OpenAI/Gemini seç ve yapılandır
   - Aktif provider'ı seç

---

## 🔐 Güvenlik

### Firewall

```bash
# Sadece gerekli portları aç
ufw allow 8000/tcp
ufw allow 22/tcp  # SSH
ufw enable
```

### SSH Key

SSH key'inizin doğru yerde olduğundan emin olun:

```bash
ls -la ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519
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
