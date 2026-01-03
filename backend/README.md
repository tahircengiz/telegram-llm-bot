# Telegram LLM Bot - Backend Service

FastAPI-based backend service for managing LLM providers, Telegram bot, and Home Assistant integration.

## Tech Stack
- FastAPI 0.109+
- SQLAlchemy 2.0+
- Pydantic v2
- Python 3.11+

## Setup

### Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Database Initialization
```bash
# Auto-created on first run
python -m backend.main
```

### Run
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables
```bash
DATABASE_URL=sqlite:///./data/bot.db
ENCRYPTION_KEY=<generate-with-cryptography>
```
