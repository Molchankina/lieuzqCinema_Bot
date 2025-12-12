# main.py - ОСНОВНОЙ ФАЙЛ ДЛЯ ЗАПУСКА (в корне проекта)

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

def check_environment():
    """Проверка переменных окружения"""
    logger.info("=" * 50)
    logger.info("Проверка окружения MovieMate Bot")
    logger.info(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # Проверяем наличие папки bot
    if not os.path.exists("bot"):
        logger.error("❌ Папка 'bot' не найдена!")
        return False

    # Проверяем наличие __init__.py
    if not os.path.exists("bot/__init__.py"):
        logger.error("❌ Файл 'bot/__init__.py' не найден!")
        return False

    # Проверяем основные файлы
    required_files = ["bot/handlers.py", "bot/database.py"]
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ Файл '{file}' не найден!")
            return False

    logger.info("✅ Структура проекта проверена")
    return True

def import_modules():
    """Импорт всех необходимых модулей"""
    logger.info("Импорт модулей...")

    try:
        # Импортируем модули из папки bot
        from bot import handlers, database, tmdb_client, db_utils
        logger.info("✅ Основные модули импортированы")

        # Проверяем наличие API клиента
        try:
            from bot import kinopoisk_client
            logger.info("✅ Модуль kinopoisk_client найден")
        except ImportError:
            logger.warning("⚠️ Модуль kinopoisk_client не найден (это нормально)")

        return handlers, database, tmdb_client, db_utils

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта модулей: {e}")

        # Показываем содержимое папки bot для отладки
        logger.info("Содержимое папки 'bot':")
        try:
            for item in os.listdir("bot"):
                logger.info(f"  - {item}")
        except:
            logger.error("  Не удалось прочитать папку 'bot'")

        return None, None, None, None

def check_required_variables():
    """Проверка обязательных переменных окружения"""
    required_vars = ['TELEGRAM_BOT_TOKEN']

    # Проверяем, какой API будем использовать
    use_tmdb = os.getenv('USE_TMDB', 'true').lower() == 'true'

    if use_tmdb:
        required_vars.append('TMDB_API_KEY')
        logger.info("Режим: Использование TMDB API")
    else:
        required_vars.append('KINOPOISK_API_KEY')
        logger.info("Режим: Использование КиноПоиск API")

    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
            logger.error(f"❌ Переменная {var} не установлена или имеет значение по умолчанию")
        else:
            logger.info(f"✅ {var} = {value[:10]}...")  # Показываем только начало

    if missing_vars:
        logger.error(f"Необходимо установить переменные: {missing_vars}")
        logger.error("Добавьте их в Railway Dashboard -> Variables")
        return False

    return True

def setup_bot_application(handlers):
    """Настройка Telegram бота"""
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        from telegram import BotCommand

        # Получаем токен бота
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN не найден!")
            return None

        # Создаем приложение
        application = Application.builder().token(token).build()
        logger.info("✅ Приложение Telegram создано")

        # Регистрируем команды
        command_handlers = [
            ("start", handlers.start),
            ("help", handlers.help_command),
            ("watchlist", handlers.show_watchlist),
            ("search", handlers.search_command),
            ("similar", handlers.similar_command),
            ("top", handlers.show_top_movies),
            ("random", handlers.random_movie),
            ("settings", handlers.show_settings),
            ("stats", handlers.user_stats),
        ]

        for cmd_name, cmd_handler in command_handlers:
            if hasattr(handlers, cmd_handler.__name__ if callable(cmd_handler) else cmd_handler):
                application.add_handler(CommandHandler(cmd_name, cmd_handler))
                logger.info(f"✅ Команда /{cmd_name} зарегистрирована")

        # Inline кнопки
        application.add_handler(CallbackQueryHandler(handlers.button_handler))
        logger.info("✅ Обработчик кнопок зарегистрирован")

        # Обработчик текстовых сообщений (включая кнопки ReplyKeyboard)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        logger.info("✅ Обработчик текстовых сообщений зарегистрирован")

        # Обработчик ошибок
        async def error_handler(update, context):
            logger.error(f"Ошибка в боте: {context.error}", exc_info=True)

        application.add_error_handler(error_handler)

        # Настройка меню команд
        async def post_init(application):
            await application.bot.set_my_commands([
                BotCommand("start", "Запустить бота с клавиатурой"),
                BotCommand("help", "Справка по командам"),
                BotCommand("search", "Поиск фильмов"),
                BotCommand("similar", "Похожие фильмы"),
                BotCommand("watchlist", "Мой список просмотра"),
                BotCommand("top", "Топ фильмов"),
                BotCommand("random", "Случайный фильм"),
                BotCommand("settings", "Настройки бота"),
                BotCommand("stats", "Статистика пользователя"),
            ])
            logger.info("✅ Меню команд настроено")

        application.post_init = post_init

        return application

    except Exception as e:
        logger.error(f"❌ Ошибка настройки бота: {e}")
        return None

def main():
    """Основная функция запуска"""
    try:
        # Шаг 1: Проверка структуры проекта
        if not check_environment():
            sys.exit(1)

        # Шаг 2: Импорт модулей
        handlers, database, tmdb_client, db_utils = import_modules()
        if not all([handlers, database]):
            sys.exit(1)

        # Шаг 3: Проверка переменных окружения
        if not check_required_variables():
            sys.exit(1)

        # Шаг 4: Инициализация базы данных
        logger.info("Инициализация базы данных...")
        try:
            database.init_db()
            logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            # Продолжаем без БД

        # Шаг 5: Настройка Telegram бота
        application = setup_bot_application(handlers)
        if not application:
            sys.exit(1)

        # Шаг 6: Запуск бота
        logger.info("=" * 50)
        logger.info("🚀 ЗАПУСК MOVIEMATE BOT")
        logger.info("=" * 50)

        # Определяем режим запуска
        is_railway = os.getenv('RAILWAY_ENVIRONMENT') == 'true'
        webhook_url = os.getenv('RAILWAY_WEBHOOK_URL')

        if is_railway and webhook_url:
            # Режим webhook для Railway
            port = int(os.getenv('PORT', 8000))
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            webhook_path = f"/webhook/{token}"

            logger.info(f"🌐 Режим: WEBHOOK (порт {port})")
            logger.info(f"🌐 Webhook URL: {webhook_url}{webhook_path}")

            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=webhook_path,
                webhook_url=f"{webhook_url}{webhook_path}",
                drop_pending_updates=True
            )
        else:
            # Режим polling для локальной разработки
            logger.info("🔄 Режим: POLLING")
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )

    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    # Загружаем переменные окружения из .env файла (для локальной разработки)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("✅ .env файл загружен (локальная разработка)")
    except ImportError:
        logger.info("ℹ️ dotenv не установлен (нормально для продакшена)")

    # Проверяем версию Python
    if sys.version_info < (3, 8):
        logger.error("❌ Требуется Python 3.8 или выше")
        sys.exit(1)

    # Запускаем бота
    main()
