# Telegram LLM Bot

Web-based admin panel for managing Telegram LLM bot with multi-provider support.

## Features

- 🤖 Multi-LLM Provider Support (Ollama, OpenAI, Gemini)
- 📱 Telegram Bot Integration
- 🏠 Home Assistant Integration
- 🎨 Modern React Admin Panel
- 🐳 Containerized Deployment
- ☸️ Kubernetes Ready

## Quick Start (Development)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m backend.main
```

Visit: http://localhost:8000/api/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

## Production Deployment

See [deployment_guide.md](docs/deployment_guide.md) for complete instructions.

### Quick Deploy to K3s

```bash
# Build image
docker build -t YOUR_USERNAME/telegram-llm-bot:latest .
docker push YOUR_USERNAME/telegram-llm-bot:latest

# Update k8s/03-deployment.yaml with your image

# Deploy
kubectl apply -f k8s/

# Access admin panel
open http://192.168.7.170:30800
```

## Project Structure

```
telegram-llm-bot/
├── backend/          # FastAPI backend
│   ├── models.py     # Database models
│   ├── routers/      # API endpoints
│   └── services/     # LLM, Telegram, HA services
├── frontend/         # React admin panel
│   └── src/
│       ├── pages/    # Dashboard, Providers, Settings
│       └── api/      # API client
├── k8s/              # Kubernetes manifests
├── Dockerfile        # Multi-stage build
└── README.md
```

## Configuration

### LLM Providers

Configure via admin panel at `/providers`:

- **Ollama**: Local/K8s deployment
- **OpenAI**: API key required
- **Gemini**: API key required

### Telegram Bot

1. Create bot with @BotFather
2. Configure in admin panel at `/telegram`
3. Add allowed chat IDs

### Home Assistant

1. Configure HA URL at `/home-assistant`
2. Optional: Add long-lived access token
3. Enable dry-run mode for testing

## Tech Stack

**Backend:**
- FastAPI
- SQLAlchemy
- Python-telegram-bot
- OpenAI/Gemini SDKs

**Frontend:**
- React + TypeScript
- Material-UI
- Axios
- React Router

**Deployment:**
- Docker multi-stage build
- Kubernetes/K3s
- SQLite (dev) / PostgreSQL (prod)

## License

MIT
# Trigger frontend build
