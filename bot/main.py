# bot/main.py

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Настройка путей для корректных импортов
# Добавляем текущую директорию в sys.path для относительных импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Теперь импортируем локальные модули
try:
    import handlers
    import database
    # Импортируем только тот клиент, который будем использовать
    # Раскомментируйте нужную строку:
    import tmdb_client    # если используете TMDB с DNS
    # import kinopoisk_client  # если используете КиноПоиск
    import db_utils       # если используете утилиты БД
except ImportError as e:
    logging.error(f"Ошибка импорта модулей: {e}")
    # Пробуем альтернативный способ импорта
    try:
        from . import handlers, database, tmdb_client, db_utils
    except ImportError:
        logging.error("Не удалось импортировать модули. Проверьте структуру проекта.")
        sys.exit(1)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if os.getenv('LOG_LEVEL') != 'DEBUG' else logging.DEBUG
)
logger = logging.getLogger(__name__)

def check_required_vars():
    """Проверка обязательных переменных окружения"""
    required_vars = ['TELEGRAM_BOT_TOKEN']

    # Проверяем наличие API ключа для выбранного источника
    if hasattr(tmdb_client, 'tmdb_client') and not os.getenv('KINOPOISK_API_KEY'):
        required_vars.append('TMDB_API_KEY')
    elif hasattr(sys.modules[__name__], 'kinopoisk_client') and not os.getenv('TMDB_API_KEY'):
        required_vars.append('KINOPOISK_API_KEY')

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {missing_vars}")
        logger.error("Добавьте их в Railway Dashboard -> Variables")
        return False

    # Дополнительная проверка значений
    if os.getenv('TELEGRAM_BOT_TOKEN') == 'your_telegram_bot_token_here':
        logger.error("TELEGRAM_BOT_TOKEN не изменен. Получите токен у @BotFather")
        return False

    return True

def setup_application():
    """Настройка и создание приложения Telegram"""
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

    # Создание приложения Telegram
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Регистрация обработчиков команд
    command_handlers = [
        ("start", handlers.start),
        ("help", handlers.help_command),
        ("watchlist", handlers.show_watchlist),
        ("search", handlers.search_command),
        ("similar", handlers.similar_command),
        ("stats", handlers.user_stats),
    ]

    for command, handler in command_handlers:
        if hasattr(handlers, handler.__name__ if callable(handler) else handler):
            application.add_handler(CommandHandler(command, handler))

    # Обработчик inline-кнопок
    application.add_handler(CallbackQueryHandler(handlers.button_handler))

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))

    return application

async def post_init(application):
    """Функция, выполняемая после инициализации бота"""
    logger.info("=" * 50)
    logger.info(f"MovieMate Bot запущен")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Режим работы: {'WEBHOOK' if os.getenv('RAILWAY_ENVIRONMENT') else 'POLLING'}")
    logger.info("=" * 50)

    # Отправляем сообщение админу о запуске (опционально)
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    for admin_id in admin_ids:
        if admin_id.strip().isdigit():
            try:
                await application.bot.send_message(
                    chat_id=int(admin_id.strip()),
                    text=f"✅ MovieMate Bot запущен\nВремя: {datetime.now().strftime('%H:%M:%S')}"
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")

async def post_stop(application):
    """Функция, выполняемая при остановке бота"""
    logger.info("MovieMate Bot останавливается...")

    # Отправляем сообщение админу об остановке (опционально)
    admin_ids = os.getenv('ADMIN_IDS', '').split(',')
    for admin_id in admin_ids:
        if admin_id.strip().isdigit():
            try:
                await application.bot.send_message(
                    chat_id=int(admin_id.strip()),
                    text=f"⏸️ MovieMate Bot остановлен\nВремя: {datetime.now().strftime('%H:%M:%S')}"
                )
            except Exception as e:
                logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")

async def error_handler(update, context):
    """Глобальный обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}", exc_info=context.error)

    # Отправляем пользователю сообщение об ошибке
    if update and hasattr(update, 'effective_chat'):
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="😔 Произошла ошибка. Разработчик уже уведомлен."
            )
        except:
            pass

def run_polling(application):
    """Запуск бота в режиме polling"""
    logger.info("Запуск в режиме POLLING...")

    # Импортируем здесь, чтобы избежать циклических импортов
    from telegram.ext import Application

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=['message', 'callback_query']
    )

def run_webhook(application):
    """Запуск бота в режиме webhook (для Railway)"""
    from telegram.ext import Application

    port = int(os.getenv('PORT', 8000))
    webhook_url = os.getenv('RAILWAY_WEBHOOK_URL')
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not webhook_url:
        logger.error("RAILWAY_WEBHOOK_URL не установлен. Запускаю в режиме polling.")
        run_polling(application)
        return

    webhook_path = f"/webhook/{token}"
    full_webhook_url = f"{webhook_url}{webhook_path}"

    logger.info(f"Запуск в режиме WEBHOOK на порту {port}")
    logger.info(f"Webhook URL: {full_webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=full_webhook_url,
        secret_token=os.getenv('WEBHOOK_SECRET', 'telegram-webhook-secret'),
        drop_pending_updates=True
    )

def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем обязательные переменные
        if not check_required_vars():
            sys.exit(1)

        # Инициализация базы данных
        logger.info("Инициализация базы данных...")
        try:
            database.init_db()
            logger.info("База данных инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            # Продолжаем работу, даже если БД не инициализирована

        # Настройка приложения
        application = setup_application()

        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)

        # Настройка post_init и post_stop
        application.post_init = post_init
        application.post_stop = post_stop

        # Определяем режим запуска
        if os.getenv('RAILWAY_ENVIRONMENT') and os.getenv('RAILWAY_WEBHOOK_URL'):
            run_webhook(application)
        else:
            run_polling(application)

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # Проверка Python версии
    if sys.version_info < (3, 8):
        logger.error("Требуется Python 3.8 или выше")
        sys.exit(1)

    # Запуск бота
    main()