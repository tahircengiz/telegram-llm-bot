#!/usr/bin/env python3
"""
Test script for Telegram bot functionality
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database import init_db, SessionLocal
from backend.models import TelegramConfig, LLMProvider
from backend.services.bot_manager import get_bot_manager
from backend.utils.logger import setup_logging
import logging

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def test_bot():
    """Test bot functionality"""
    print("=" * 60)
    print("Telegram Bot Test Script")
    print("=" * 60)
    
    # Initialize database
    print("\n[1/5] Initializing database...")
    init_db()
    print("✅ Database initialized")
    
    # Check config
    print("\n[2/5] Checking Telegram config...")
    db = SessionLocal()
    try:
        config = db.query(TelegramConfig).first()
        
        if not config:
            print("❌ No Telegram config found. Please configure via admin panel first.")
            print("   Steps:")
            print("   1. Start the application")
            print("   2. Go to http://localhost:8000")
            print("   3. Navigate to Telegram Settings")
            print("   4. Add bot token and enable bot")
            return False
        
        print(f"   Bot Token: {'***' + config.bot_token[-10:] if len(config.bot_token) > 10 else 'Not set'}")
        print(f"   Enabled: {config.enabled}")
        print(f"   Rate Limit: {config.rate_limit}/min")
        print(f"   Allowed Chat IDs: {config.allowed_chat_ids}")
        
        if not config.bot_token:
            print("❌ Bot token not set!")
            return False
        
        if not config.enabled:
            print("⚠️  Bot is disabled. Enable it in config.")
            return False
        
        print("✅ Config found")
    
    finally:
        db.close()
    
    # Check LLM provider
    print("\n[3/5] Checking LLM provider...")
    db = SessionLocal()
    try:
        provider = db.query(LLMProvider).filter(LLMProvider.active == True).first()
        if provider:
            print(f"   Active Provider: {provider.name}")
            print("✅ LLM provider configured")
        else:
            print("⚠️  No active LLM provider found")
    finally:
        db.close()
    
    # Test bot manager
    print("\n[4/5] Testing bot manager...")
    try:
        manager = get_bot_manager()
        bot = await manager.get_bot()
        
        if bot:
            print("✅ Bot instance created")
            print(f"   Bot running: {manager.is_running()}")
        else:
            print("❌ Failed to create bot instance")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Final status
    print("\n[5/5] Final status...")
    print("=" * 60)
    print("✅ All tests passed!")
    print("\nBot should be running and ready to receive messages.")
    print("Send a message to your bot on Telegram to test.")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_bot())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
