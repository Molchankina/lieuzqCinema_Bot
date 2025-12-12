# main.py - упрощенная версия для КиноПоиска

import os
import sys
import logging
from datetime import datetime

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_api_status():
    """Проверка статуса API"""
    try:
        from bot.kinopoisk_client import kinopoisk_client

        if kinopoisk_client.is_active:
            logger.info("✅ КиноПоиск API активен")
            return True
        else:
            logger.error("❌ КиноПоиск API не активен")
            logger.error("Установите KINOPOISK_API_KEY в .env файле")
            return False

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта КиноПоиск клиента: {e}")
        return False

def main():
    """Основная функция запуска"""
    logger.info("=" * 50)
    logger.info("Запуск MovieMate Bot (КиноПоиск)")
    logger.info(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # Проверяем API
    if not check_api_status():
        logger.warning("⚠️ Бот запускается без активного API")

    # Проверяем токен бота
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token or token.startswith('your_'):
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        logger.error("Получите токен у @BotFather и добавьте в .env")
        sys.exit(1)

    # Импортируем модули
    try:
        from bot import handlers, database
        logger.info("✅ Модули импортированы")
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта модулей: {e}")
        sys.exit(1)

    # Инициализация базы данных
    try:
        database.init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка инициализации БД: {e}")

    # Создаем приложение Telegram
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

        application = Application.builder().token(token).build()
        logger.info("✅ Приложение Telegram создано")

        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("help", handlers.help_command))
        application.add_handler(CommandHandler("search", handlers.search_command))
        application.add_handler(CommandHandler("top", handlers.show_top250))
        application.add_handler(CommandHandler("random", handlers.random_movie))
        application.add_handler(CommandHandler("watchlist", handlers.show_watchlist))

        # Inline кнопки
        application.add_handler(CallbackQueryHandler(handlers.button_handler))

        # Текстовые сообщения
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

        logger.info("✅ Все обработчики зарегистрированы")

        # Запускаем бота
        logger.info("🔄 Запуск бота в режиме polling...")
        application.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # Загружаем .env файл для локальной разработки
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ .env файл загружен")
    except ImportError:
        logger.info("ℹ️ dotenv не установлен (нормально для Railway)")

    main()