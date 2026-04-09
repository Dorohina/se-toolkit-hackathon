"""
Main entry point for the Event Finder Telegram Bot.
"""

import logging
import asyncio
from telegram.ext import ApplicationBuilder
from config import settings
from database import init_db, close_db, async_session_maker
from bot import register_handlers

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Initialize database after application starts."""
    await init_db()
    logger.info("Database initialized")


async def shutdown(application):
    """Close database connections on shutdown."""
    await close_db()
    logger.info("Database connections closed")


def main():
    """Start the bot."""
    logger.info("Starting Event Finder Bot...")
    
    # Build the application
    application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(shutdown)
        .build()
    )
    
    # Register handlers
    register_handlers(application)
    
    # Run bot
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()
