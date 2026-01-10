from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .config import settings
from .database import init_db, get_db
from .models import LLMProvider
from .routers import providers, telegram, home_assistant
from .services import bot_manager
from .utils.logger import setup_logging
import asyncio
import logging

# Setup logging
setup_logging(level="INFO" if not settings.debug else "DEBUG", use_json=False)
logger = logging.getLogger(__name__)

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

# Include routers FIRST (before static files)
app.include_router(providers.router)
app.include_router(telegram.router)
app.include_router(home_assistant.router)


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
        
        # Start Telegram bot if configured (using BotManager)
        from .models import TelegramConfig
        telegram_config = db.query(TelegramConfig).first()
        if telegram_config and telegram_config.enabled and telegram_config.bot_token:
            logger.info("Starting Telegram bot on startup...")
            try:
                manager = bot_manager.get_bot_manager()
                bot = await manager.get_bot(db)
                if bot:
                    logger.info("✅ Telegram bot started successfully via BotManager")
                else:
                    logger.error("❌ Failed to start Telegram bot")
            except Exception as e:
                logger.error(f"Error starting Telegram bot: {e}", exc_info=True)
        else:
            logger.info("Telegram bot not configured or disabled, skipping startup")
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


# Serve frontend - MUST be after all API routes
frontend_path = settings.frontend_dir or "/app/frontend/dist"
if os.path.exists(frontend_path):
    print(f"✅ Serving frontend from: {frontend_path}")
    
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")
    
    # Catch-all route for SPA (MUST be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all non-API routes"""
        # Don't serve for API routes (already handled above)
        if full_path.startswith("api/"):
            return None
        
        # Serve index.html for all other routes (SPA routing)
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        
        return {"detail": "Frontend not found"}
else:
    print(f"⚠️  Frontend not found at: {frontend_path}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
