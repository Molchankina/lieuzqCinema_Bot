# bot/handlers.py - с кнопками быстрого действия

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# Импортируем нужный API клиент
try:
    # Пробуем импортировать TMDB
    from . import tmdb_client
    api_client = tmdb_client.tmdb_client
    logger.info("✅ Используется TMDB клиент")
except ImportError:
    try:
        # Пробуем импортировать КиноПоиск
        from . import kinopoisk_client
        api_client = kinopoisk_client.kinopoisk_client
        logger.info("✅ Используется КиноПоиск клиент")
    except ImportError:
        logger.error("❌ Не найден ни один API клиент!")
        api_client = None

# Импортируем утилиты БД
try:
    from .db_utils import get_db_manager
    db_manager = get_db_manager()
    logger.info("✅ Менеджер БД инициализирован")
except ImportError as e:
    logger.warning(f"⚠️ Модуль db_utils не найден, БД недоступна: {e}")
    db_manager = None
except Exception as e:
    logger.error(f"❌ Ошибка инициализации БД: {e}")
    db_manager = None

# Определения состояний для ConversationHandler
SEARCH, SIMILAR, ADD_MOVIE = range(3)

def get_main_keyboard():
    """Основная клавиатура быстрых действий"""
    keyboard = [
        ["🔍 Поиск фильма", "🎯 Похожие фильмы"],
        ["📋 Мой Watchlist", "⭐ Топ фильмы"],
        ["🎬 Случайный фильм", "ℹ️ Помощь"],
        ["⚙️ Настройки"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_watchlist_keyboard():
    """Клавиатура для работы с watchlist"""
    keyboard = [
        ["📥 Добавить в Watchlist", "📤 Удалить из Watchlist"],
        ["✅ Отметить просмотренным", "📋 Показать Watchlist"],
        ["🔙 На главную"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_search_keyboard():
    """Клавиатура для поиска"""
    keyboard = [
        ["🎭 По жанру", "📅 По году"],
        ["⭐ По рейтингу", "🔍 Общий поиск"],
        ["🔙 На главную"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с клавиатурой"""
    user = update.effective_user

    welcome_text = f"""
🎬 Привет, {user.first_name}! Я MovieMate — твой персональный киногид!

✨ *Что я умею:*
• 🔍 Искать фильмы и сериалы
• 🎯 Подбирать похожие фильмы
• 💾 Сохранять в «Посмотреть позже»
• 🔔 Напоминать о новых сериях
• 🎲 Рекомендовать случайные фильмы

💡 *Используй кнопки ниже или команды:*
• Напиши «Хочу детектив 90-х»
• Или используй /search <название>
    """

    # Отправляем приветствие с основной клавиатурой
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

    # Также отправляем inline клавиатуру для дополнительных действий
    inline_keyboard = [
        [InlineKeyboardButton("🚀 Быстрый поиск", callback_data="quick_search")],
        [InlineKeyboardButton("🎲 Случайный фильм", callback_data="random_movie")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(
        "Выберите дополнительное действие:",
        reply_markup=reply_markup
    )

    # Регистрируем пользователя в БД
    if db_manager:
        try:
            db_manager.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📚 *Доступные команды:*

/start - Запустить бота с клавиатурой
/help - Эта справка
/search <запрос> - Поиск фильмов
/similar <название> - Похожие фильмы
/watchlist - Мой список для просмотра
/top - Топ фильмов
/random - Случайный фильм
/settings - Настройки бота

🎯 *Быстрые кнопки:*
• 🔍 Поиск фильма - поиск по разным критериям
• 📋 Мой Watchlist - управление списком
• 🎲 Случайный фильм - рекомендация
• ⚙️ Настройки - настройки бота

💡 *Примеры запросов:*
• «Хочу детектив 90-х»
• «Поиск: Матрица»
• «Что посмотреть, если нравится Интерстеллар?»
    """
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений и кнопок быстрого действия"""
    text = update.message.text.lower()

    # Обработка кнопок быстрого действия
    if text == "🔍 поиск фильма":
        await update.message.reply_text(
            "Выберите тип поиска:",
            reply_markup=get_search_keyboard()
        )

    elif text == "🎯 похожие фильмы":
        await update.message.reply_text(
            "Введите название фильма, чтобы найти похожие:\n"
            "Например: *Матрица* или *Интерстеллар*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'similar'

    elif text == "📋 мой watchlist":
        await show_watchlist(update, context)

    elif text == "⭐ топ фильмов":
        await show_top_movies(update, context)

    elif text == "🎬 случайный фильм":
        await random_movie(update, context)

    elif text == "ℹ️ помощь":
        await help_command(update, context)

    elif text == "⚙️ настройки":
        await show_settings(update, context)

    elif text == "🔙 на главную":
        await update.message.reply_text(
            "Возвращаю на главную...",
            reply_markup=get_main_keyboard()
        )

    elif text == "🎭 по жанру":
        await search_by_genre(update, context)

    elif text == "📅 по году":
        await search_by_year(update, context)

    elif text == "⭐ по рейтингу":
        await search_by_rating(update, context)

    elif text == "🔍 общий поиск":
        await update.message.reply_text(
            "Введите название фильма или сериала для поиска:"
        )
        context.user_data['waiting_for'] = 'search'

    # Обработка ввода после нажатия кнопки
    elif 'waiting_for' in context.user_data:
        if context.user_data['waiting_for'] == 'search':
            await search_command(update, context, text)
            context.user_data.pop('waiting_for', None)
        elif context.user_data['waiting_for'] == 'similar':
            await similar_command(update, context, text)
            context.user_data.pop('waiting_for', None)

    # Старая логика обработки текстовых запросов
    elif any(word in text for word in ['хочу', 'ищи', 'найди', 'поиск:', 'search:']):
        query = text.split(':', 1)[-1].strip() if ':' in text else text
        await search_command(update, context, query)

    elif 'похож' in text or 'если нравится' in text:
        query = text.split('если нравится', 1)[-1].strip() if 'если нравится' in text else text
        await similar_command(update, context, query)

    elif 'детектив' in text and '90' in text:
        await update.message.reply_text("🔍 Ищу детективы 90-х годов...")
        await search_by_genre_year(update, context, genre="детектив", year="1990")

    elif 'комедия' in text:
        await update.message.reply_text("🔍 Ищу комедии...")
        await search_by_genre_year(update, context, genre="комедия")

    else:
        await update.message.reply_text(
            "Не совсем понял запрос 🤔\n\n"
            "Попробуй:\n"
            "• Использовать кнопки ниже\n"
            "• Или напиши: «Хочу детектив 90-х»",
            reply_markup=get_main_keyboard()
        )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    """Обработчик команды /search"""
    if not query:
        if context.args:
            query = ' '.join(context.args)
        else:
            await update.message.reply_text(
                "Введите название фильма для поиска:",
                reply_markup=get_main_keyboard()
            )
            return

    await update.message.reply_text(f"🔍 Ищу: *{query}*...", parse_mode='Markdown')

    if not api_client:
        await update.message.reply_text("❌ API клиент не настроен")
        return

    try:
        # Пробуем разные методы поиска в зависимости от клиента
        if hasattr(api_client, 'search_movies'):
            results = api_client.search_movies(query)
        elif hasattr(api_client, 'search_films'):
            results = api_client.search_films(query).get('films', [])[:5]
        else:
            await update.message.reply_text("❌ Метод поиска не поддерживается")
            return

        if not results:
            await update.message.reply_text("😔 Ничего не найдено. Попробуй другой запрос.")
            return

        # Показываем результаты с inline кнопками
        for i, item in enumerate(results[:3], 1):
            if isinstance(item, dict):
                title = item.get('title') or item.get('nameRu') or item.get('name', 'Без названия')
                year = item.get('release_date', '')[:4] or item.get('year', '')
                rating = item.get('vote_average') or item.get('ratingKinopoisk', '?')

                text = f"*{title}*"
                if year:
                    text += f" ({year})"
                if rating and rating != '?':
                    text += f"\n⭐ Рейтинг: {rating}/10"

                if item.get('overview') or item.get('description'):
                    desc = item.get('overview') or item.get('description', '')
                    text += f"\n\n{desc[:150]}..."

                # Кнопки действий
                keyboard = [[
                    InlineKeyboardButton("💾 В Watchlist", callback_data=f"add_{item.get('id') or item.get('filmId')}"),
                    InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{item.get('id') or item.get('filmId')}")
                ]]

                if item.get('poster_path') or item.get('posterUrlPreview'):
                    poster = item.get('poster_path') or item.get('posterUrlPreview')
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster and not poster.startswith('http') else poster

                    try:
                        await update.message.reply_photo(
                            photo=poster_url if poster_url.startswith('http') else None,
                            caption=text,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        continue
                    except:
                        pass

                await update.message.reply_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        await update.message.reply_text("❌ Ошибка при поиске")

async def similar_command(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    """Обработчик команды /similar"""
    if not query:
        if context.args:
            query = ' '.join(context.args)
        else:
            await update.message.reply_text("Укажи фильм: /similar Матрица")
            return

    await update.message.reply_text(f"🎯 Ищу похожее на: *{query}*...", parse_mode='Markdown')

    # Сначала ищем фильм
    try:
        if hasattr(api_client, 'search_movies'):
            results = api_client.search_movies(query)
            if results:
                film_id = results[0].get('id')
                similar = api_client.get_similar_movies(film_id) if hasattr(api_client, 'get_similar_movies') else []
        elif hasattr(api_client, 'search_films'):
            results = api_client.search_films(query).get('films', [])
            if results:
                film_id = results[0].get('filmId')
                similar = api_client.get_similar_films(film_id).get('items', []) if hasattr(api_client, 'get_similar_films') else []
        else:
            similar = []

        if not similar:
            await update.message.reply_text("😔 Не нашёл похожих фильмов.")
            return

        text = f"🎯 *Похоже на {query}:*\n\n"
        for i, item in enumerate(similar[:5], 1):
            title = item.get('title') or item.get('nameRu') or item.get('name', 'Без названия')
            year = item.get('release_date', '')[:4] or item.get('year', '')
            rating = item.get('vote_average') or item.get('rating', '?')

            text += f"{i}. *{title}*"
            if year:
                text += f" ({year})"
            if rating and rating != '?':
                text += f" ⭐ {rating}"
            text += "\n"

        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка поиска похожих: {e}")
        await update.message.reply_text("❌ Ошибка при поиске похожих фильмов")

async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать watchlist"""
    if not db_manager:
        await update.message.reply_text("❌ База данных не настроена")
        return

    user_id = update.effective_user.id

    try:
        watchlist = db_manager.get_watchlist(user_id)

        if not watchlist:
            await update.message.reply_text(
                "📭 Твой Watchlist пуст!\n\n"
                "Добавляй фильмы кнопкой «💾 В Watchlist» в результатах поиска.",
                reply_markup=get_watchlist_keyboard()
            )
            return

        text = "📋 *Твой Watchlist:*\n\n"
        for i, item in enumerate(watchlist[:10], 1):
            text += f"{i}. *{item['title']}*"
            if item.get('year'):
                text += f" ({item['year']})"
            text += f"\nДобавлено: {item['added_at'].strftime('%d.%m.%Y')}\n\n"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_watchlist_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения watchlist: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке Watchlist")

async def show_top_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать топ фильмов"""
    await update.message.reply_text(
        "🎬 *Топ фильмов:*\n\n"
        "1. *Побег из Шоушенка* (1994) ⭐ 9.3\n"
        "2. *Крестный отец* (1972) ⭐ 9.2\n"
        "3. *Темный рыцарь* (2008) ⭐ 9.0\n"
        "4. *Крестный отец 2* (1974) ⭐ 9.0\n"
        "5. *12 разгневанных мужчин* (1957) ⭐ 9.0\n\n"
        "💡 *Используй /search для поиска*",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайный фильм"""
    import random

    movies = [
        {"title": "Начало", "year": "2010", "rating": "8.8", "genre": "фантастика, триллер"},
        {"title": "Зеленая миля", "year": "1999", "rating": "9.1", "genre": "драма, фэнтези"},
        {"title": "Форрест Гамп", "year": "1994", "rating": "8.8", "genre": "драма, мелодрама"},
        {"title": "Бойцовский клуб", "year": "1999", "rating": "8.8", "genre": "триллер, драма"},
        {"title": "Поймай меня, если сможешь", "year": "2002", "rating": "8.1", "genre": "криминал, драма"},
    ]

    movie = random.choice(movies)

    text = f"🎲 *Случайный фильм для тебя:*\n\n"
    text += f"🎬 *{movie['title']}* ({movie['year']})\n"
    text += f"⭐ Рейтинг: {movie['rating']}/10\n"
    text += f"🎭 Жанр: {movie['genre']}\n\n"
    text += "Хочешь посмотреть?"

    keyboard = [[
        InlineKeyboardButton("🔍 Подробнее", callback_data=f"info_{movie['title']}"),
        InlineKeyboardButton("🎲 Еще один", callback_data="random_another")
    ]]

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать настройки"""
    text = """
⚙️ *Настройки MovieMate*

🔧 *Основные настройки:*
• Источник данных: TMDB
• Язык интерфейса: Русский
• Уведомления: Включены

🎯 *Быстрые команды:*
• /settings - эти настройки
• /help - справка по командам
• /start - перезапустить бота

💡 *Используй кнопки ниже для быстрого доступа к функциям!*
    """

    keyboard = [[
        InlineKeyboardButton("🔄 Сменить источник", callback_data="change_source"),
        InlineKeyboardButton("🔔 Уведомления", callback_data="notifications")
    ]]

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по жанру"""
    keyboard = [
        [InlineKeyboardButton("🎭 Драма", callback_data="genre_drama")],
        [InlineKeyboardButton("😂 Комедия", callback_data="genre_comedy")],
        [InlineKeyboardButton("🔫 Боевик", callback_data="genre_action")],
        [InlineKeyboardButton("👻 Ужасы", callback_data="genre_horror")],
        [InlineKeyboardButton("🔍 Детектив", callback_data="genre_detective")],
        [InlineKeyboardButton("🚀 Фантастика", callback_data="genre_scifi")],
    ]

    await update.message.reply_text(
        "🎭 *Выберите жанр:*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_by_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по году"""
    await update.message.reply_text(
        "📅 *Введите год выпуска фильма:*\n"
        "Например: *1999* или *2000-2010* для диапазона",
        parse_mode='Markdown'
    )
    context.user_data['waiting_for'] = 'year_search'

async def search_by_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск по рейтингу"""
    await update.message.reply_text(
        "⭐ *Введите минимальный рейтинг (от 0 до 10):*\n"
        "Например: *7.5* или *8.0*",
        parse_mode='Markdown'
    )
    context.user_data['waiting_for'] = 'rating_search'

async def search_by_genre_year(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str, year: str = None):
    """Поиск по жанру и году"""
    text = f"🔍 Ищу *{genre}*"
    if year:
        text += f" за *{year}* год"

    await update.message.reply_text(text + "...", parse_mode='Markdown')
    await update.message.reply_text("ℹ️ Эта функция в разработке")

async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика пользователя"""
    user = update.effective_user
    stats_text = f"""
📊 *Твоя статистика:*

👤 *Профиль:*
• Имя: {user.first_name or 'Не указано'}
• Username: @{user.username or 'Не указан'}
• ID: {user.id}

🎬 *Активность:*
• Фильмов в Watchlist: 0
• Просмотрено фильмов: 0
• Поисковых запросов: 0

✨ MovieMate всегда готов помочь с поиском фильмов!
    """
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий inline-кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('add_'):
        # Добавление в watchlist
        item_id = data.split('_')[1]
        await query.edit_message_text(f"✅ Добавлено в Watchlist (ID: {item_id})")

    elif data.startswith('similar_'):
        # Поиск похожих
        item_id = data.split('_')[1]
        await query.edit_message_text(f"🎯 Ищу похожие на фильм ID: {item_id}...")

    elif data.startswith('info_'):
        # Информация о фильме
        title = data.split('_')[1]
        await query.edit_message_text(f"🎬 Информация о фильме '{title}'...")

    elif data == "random_another":
        # Еще случайный фильм
        await random_movie(query, context)

    elif data == "quick_search":
        await query.edit_message_text(
            "🚀 *Быстрый поиск*\n\n"
            "Введите название фильма:",
            parse_mode='Markdown'
        )

    elif data == "stats":
        await user_stats(query, context)

    elif data.startswith("genre_"):
        genre = data.split('_')[1]
        await query.edit_message_text(f"🔍 Ищу фильмы жанра: {genre}...")

    else:
        await query.edit_message_text(f"Кнопка: {data}")