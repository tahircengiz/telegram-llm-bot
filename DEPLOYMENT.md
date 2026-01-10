# Telegram LLM Bot - GitOps Deployment Guide

## 🚀 Quick Setup

### 1. Create GitHub Repository

```bash
# Create private repo on GitHub
gh repo create telegram-llm-bot --private --description "Telegram LLM Bot with Admin Panel"

# Or create manually at: https://github.com/new
# Name: telegram-llm-bot
# Visibility: Private
```

### 2. Push Code to GitHub

```bash
cd /Users/tacengiz/Documents/projects/prj_Kahya/telegram-llm-bot

# Add remote
git remote add origin https://github.com/tacengiz/telegram-llm-bot.git

# Push
git push -u origin main
```

### 3. Verify GitHub Actions

```bash
# Go to: https://github.com/tacengiz/telegram-llm-bot/actions
# First workflow will auto-trigger
# Wait for Docker build to complete (~3-5 min)
```

### 4. Deploy to ArgoCD

```bash
# Apply ArgoCD application
kubectl apply -f argocd/application.yaml -n argocd

# Or via ArgoCD UI:
# URL: https://192.168.7.170:8088
# User: admin
# Password: 47-6KC1XjWfRvz4K
# Click "New App" → Use argocd/application.yaml values
```

### 5. Monitor Deployment

```bash
# Watch ArgoCD sync
argocd app get telegram-llm-bot --refresh

# Watch pods
kubectl get pods -n telegram-llm-bot -w

# Check logs
kubectl logs -n telegram-llm-bot deployment/telegram-llm-bot
```

### 6. Access Application

- **Frontend:** http://192.168.7.170:30800
- **API Docs:** http://192.168.7.170:30800/api/docs
- **Health:** http://192.168.7.170:30800/api/health

---

## 📋 Architecture

### CI Pipeline (GitHub Actions)
```
Push to main
  ↓
GitHub Actions triggers
  ↓
Multi-stage Docker build (frontend + backend)
  ↓
Push to ghcr.io/tacengiz/telegram-llm-bot:latest
  ↓
Push to ghcr.io/tacengiz/telegram-llm-bot:main-sha-xxxxx
```

### CD Pipeline (ArgoCD)
```
ArgoCD monitors Git repo
  ↓
Detects changes in k8s/ folder
  ↓
Auto-syncs to K3s cluster
  ↓
Creates/updates namespace telegram-llm-bot
  ↓
Deploys pods with latest image from GHCR
  ↓
Self-heals if manual changes detected
```

---

## 🔧 Common Operations

### Make Code Changes
```bash
# Edit files
vim frontend/src/App.tsx

# Commit and push
git add .
git commit -m "feat: update UI"
git push

# Automatic:
# 1. GitHub Actions builds new image
# 2. ArgoCD detects change
# 3. Deploys to K3s
# 4. Pods restart with new image
```

### Manual Sync (if needed)
```bash
# Via CLI
argocd app sync telegram-llm-bot

# Via UI
# Go to ArgoCD UI → Apps → telegram-llm-bot → SYNC
```

### Rollback
```bash
# Via Git
git revert HEAD
git push

# ArgoCD will auto-sync to previous version

# Or via ArgoCD UI
# History → Select previous revision → SYNC TO
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/telegram-llm-bot -n telegram-llm-bot

# ArgoCD sync logs
argocd app logs telegram-llm-bot --follow
```

---

## 🔐 Security

### GitHub Container Registry
- Packages are private by default
- K3s needs imagePullSecret for private images
- Currently using public GHCR (no credential needed)
- To make private: Add imagePullSecret to deployment

### Image Pull Secret (if private)
```bash
# Create secret
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=tacengiz \
  --docker-password=<GITHUB_PAT> \
  --docker-email=your@email.com \
  -n telegram-llm-bot

# Add to deployment spec
spec:
  template:
    spec:
      imagePullSecrets:
      - name: ghcr-secret
```

---

## 📊 Monitoring

### ArgoCD Health Status
```bash
# CLI
argocd app get telegram-llm-bot

# Returns:
# - Sync Status: Synced/OutOfSync
# - Health Status: Healthy/Progressing/Degraded
# - Last Sync: timestamp
```

### Application Status
```bash
# Pods
kubectl get pods -n telegram-llm-bot

# Services
kubectl get svc -n telegram-llm-bot

# PVCs
kubectl get pvc -n telegram-llm-bot
```

---

## 🐛 Troubleshooting

### Image Pull Errors
```bash
# Check events
kubectl describe pod <pod-name> -n telegram-llm-bot

# Common fixes:
# 1. Ensure GitHub Actions completed successfully
# 2. Check image exists: https://github.com/tacengiz?tab=packages
# 3. Verify imagePullPolicy in deployment
```

### ArgoCD Not Syncing
```bash
# Check app status
argocd app get telegram-llm-bot

# Force refresh
argocd app get telegram-llm-bot --refresh --hard

# Manual sync
argocd app sync telegram-llm-bot --force
```

### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs <pod-name> -n telegram-llm-bot

# Check previous logs
kubectl logs <pod-name> -n telegram-llm-bot --previous

# Common issues:
# - Database migration errors
# - Missing environment variables
# - Frontend build failures
```

---

## 🎯 Next Steps

1. ✅ Push code to GitHub
2. ✅ Verify GitHub Actions build
3. ✅ Apply ArgoCD application
4. ⏳ Configure Telegram bot token
5. ⏳ Test admin panel features
6. ⏳ Monitor first auto-deployment

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

## 📚 Resources

- **GitHub Actions:** https://github.com/tacengiz/telegram-llm-bot/actions
- **GHCR Packages:** https://github.com/tacengiz?tab=packages
- **ArgoCD UI:** https://192.168.7.170:8088
- **Application:** http://192.168.7.170:30800
