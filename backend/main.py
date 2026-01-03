from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from .config import settings
from .database import init_db, get_db
from .models import LLMProvider
from .routers import providers, telegram

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(providers.router)
app.include_router(telegram.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and create default providers"""
    init_db()
    
    # Create default LLM providers if not exist
    db = next(get_db())
    try:
        providers = ["ollama", "openai", "gemini"]
        for provider_name in providers:
            existing = db.query(LLMProvider).filter(LLMProvider.name == provider_name).first()
            if not existing:
                provider = LLMProvider(
                    name=provider_name,
                    enabled=(provider_name == "ollama"),  # Ollama enabled by default
                    active=(provider_name == "ollama")    # Ollama active by default
                )
                db.add(provider)
        db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.version
    }


@app.get("/api/status")
def system_status(db: Session = Depends(get_db)):
    """Get system status"""
    active_provider = db.query(LLMProvider).filter(LLMProvider.active == True).first()
    
    return {
        "active_provider": active_provider.name if active_provider else None,
        "database": "connected",
        "telegram_bot": "not_configured"  # Will be updated
    }


# Serve frontend if available
if settings.frontend_dir and os.path.exists(settings.frontend_dir):
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
