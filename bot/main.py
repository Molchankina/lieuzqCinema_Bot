import os
import logging
import handlers
import database
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Error: {context.error}", exc_info=context.error)

    # Notify user about error
    if update and update.effective_chat:
        try:
            await update.effective_chat.send_message(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except:
            pass

def main():
    """Start the bot"""
    # Check required environment variables
    required_vars = ['TELEGRAM_BOT_TOKEN', 'TMDB_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        raise ValueError(f"Please set environment variables: {missing_vars}")

    # Initialize database
    database.init_db()

    # Create Telegram application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Register handlers
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("watchlist", handlers.show_watchlist))
    application.add_handler(CommandHandler("search", handlers.search_command))
    application.add_handler(CommandHandler("similar", handlers.similar_command))
    application.add_handler(CommandHandler("stats", handlers.user_stats))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))

    # Text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    webhook_url = os.getenv('RAILWAY_WEBHOOK_URL')
    railway_environment = os.getenv('RAILWAY_ENVIRONMENT')

    if webhook_url and railway_environment:
        # Webhook mode for Railway
        port = int(os.getenv('PORT', 8000))
        webhook_path = f"/webhook/{os.getenv('TELEGRAM_BOT_TOKEN')}"

        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=f"{webhook_url}{webhook_path}",
            secret_token=os.getenv('WEBHOOK_SECRET', 'telegram-webhook-secret')
        )
        logger.info(f"Bot running in webhook mode on port {port}")
    else:
        # Polling mode for local development
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        logger.info("Bot running in polling mode")

if __name__ == '__main__':
    main()