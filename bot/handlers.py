# bot/handlers.py - оптимизирован для КиноПоиска

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Импортируем только КиноПоиск клиент
try:
    from .kinopoisk_client import kinopoisk_client
    api_client = kinopoisk_client
    logger.info(f"✅ Используется КиноПоиск клиент. Статус: {'АКТИВЕН' if api_client.is_active else 'НЕ АКТИВЕН'}")
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать КиноПоиск клиент: {e}")
    api_client = None

# Импортируем утилиты БД
try:
    from .db_utils import get_db_manager
    db_manager = get_db_manager()
    logger.info("✅ Менеджер БД инициализирован")
except ImportError as e:
    logger.warning(f"⚠️ Модуль db_utils не найден: {e}")
    db_manager = None

# Карта жанров для поиска
GENRE_MAP = {
    "драма": 1,
    "комедия": 13,
    "боевик": 11,
    "триллер": 4,
    "фантастика": 6,
    "ужасы": 7,
    "детектив": 3,
    "мелодрама": 22,
    "приключения": 12,
    "фэнтези": 14,
    "мультфильм": 16,
    "биография": 5,
    "вестерн": 10,
    "история": 18,
    "криминал": 8,
    "документальный": 9
}

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = [
        ["🔍 Поиск фильма", "🎭 По жанру"],
        ["⭐ Топ 250", "🎲 Случайный"],
        ["📋 Мой Watchlist", "ℹ️ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_genre_keyboard():
    """Клавиатура жанров"""
    keyboard = [
        ["🎭 Драма", "😂 Комедия", "🔫 Боевик"],
        ["👻 Ужасы", "🚀 Фантастика", "🔍 Детектив"],
        ["❤️ Мелодрама", "🧩 Триллер", "🎬 Приключения"],
        ["🔙 На главную"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Проверяем API статус
    api_status = "✅ КиноПоиск активен" if api_client and api_client.is_active else "❌ КиноПоиск не настроен"

    welcome_text = f"""
🎬 Привет, {user.first_name}! Я MovieMate — твой киногид!

{api_status}

✨ *Что я умею:*
• 🔍 Искать фильмы и сериалы
• 🎯 Подбирать похожие фильмы  
• 💾 Сохранять в «Посмотреть позже»
• 🎲 Рекомендовать случайные фильмы
• ⭐ Показывать топ-250 лучших фильмов

💡 *Используй кнопки ниже для быстрого доступа!*
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

    # Регистрируем пользователя
    if db_manager:
        try:
            db_manager.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📚 *MovieMate Bot — помощник по фильмам*

🎯 *Основные функции:*
• Поиск фильмов и сериалов
• Топ-250 лучших фильмов
• Подбор по жанрам
• Случайные рекомендации
• Список «Посмотреть позже»

⌨️ *Используй кнопки или команды:*
• /search <название> — поиск фильма
• /top — топ-250 фильмов  
• /random — случайный фильм
• /watchlist — мой список
• /genres — список жанров

🎬 *Примеры запросов:*
• «Матрица»
• «Детектив 90-х»
• «Лучшие комедии 2000-х»
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()

    # Обработка кнопок
    if text == "🔍 поиск фильма":
        await update.message.reply_text(
            "Введите название фильма или сериала:\n"
            "Например: *Матрица* или *Игра престолов*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'search'

    elif text == "🎭 по жанру":
        await update.message.reply_text(
            "Выберите жанр:",
            reply_markup=get_genre_keyboard()
        )

    elif text == "⭐ топ 250":
        await show_top250(update, context)

    elif text == "🎲 случайный":
        await random_movie(update, context)

    elif text == "📋 мой watchlist":
        await show_watchlist(update, context)

    elif text == "ℹ️ помощь":
        await help_command(update, context)

    elif text == "🔙 на главную":
        await update.message.reply_text(
            "Возвращаю на главную...",
            reply_markup=get_main_keyboard()
        )

    # Обработка жанров
    elif text in ["🎭 драма", "😂 комедия", "🔫 боевик", "👻 ужасы",
                  "🚀 фантастика", "🔍 детектив", "❤️ мелодрама",
                  "🧩 триллер", "🎬 приключения"]:
        genre = text.split(' ')[1]  # Извлекаем название жанра
        await search_by_genre(update, context, genre)

    # Обработка ввода после нажатия кнопки
    elif 'waiting_for' in context.user_data:
        if context.user_data['waiting_for'] == 'search':
            await search_command(update, context, text)
            context.user_data.pop('waiting_for', None)

    # Прямые текстовые запросы
    elif text and len(text) > 2:
        await search_command(update, context, text)

    else:
        await update.message.reply_text(
            "Введите название фильма для поиска или используйте кнопки ниже 👇",
            reply_markup=get_main_keyboard()
        )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    """Поиск фильмов через КиноПоиск"""
    if not query:
        if context.args:
            query = ' '.join(context.args)
        else:
            await update.message.reply_text("Введите название фильма для поиска:")
            return

    if not api_client or not api_client.is_active:
        await update.message.reply_text(
            "❌ КиноПоиск API не настроен.\n\n"
            "Для работы бота нужно:\n"
            "1. Получить API ключ на https://kinopoiskapiunofficial.tech\n"
            "2. Добавить KINOPOISK_API_KEY в .env файл"
        )
        return

    await update.message.reply_text(f"🔍 Ищу: *{query}*...", parse_mode='Markdown')

    try:
        # Выполняем поиск
        result = api_client.search_films(query)
        films = result.get('films', [])

        if not films:
            await update.message.reply_text(
                f"😔 По запросу «{query}» ничего не найдено.\n\n"
                "Попробуйте:\n"
                "• Уточнить название\n"
                "• Использовать русское название\n"
                "• Попробовать другой фильм"
            )
            return

        # Показываем первые 3 результата
        for i, film in enumerate(films[:3], 1):
            title = film.get('nameRu') or film.get('nameEn') or 'Без названия'
            year = film.get('year', '')
            rating = film.get('rating', '')
            film_id = film.get('filmId')

            # Формируем текст
            text = f"*{title}*"
            if year:
                text += f" ({year})"

            if rating:
                text += f"\n⭐ Рейтинг: {rating}"

            # Описание если есть
            description = film.get('description', '')
            if description:
                text += f"\n\n{description[:150]}..."

            # Кнопки действий
            keyboard = [[
                InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{film_id}"),
                InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{film_id}")
            ]]

            # Постер если есть
            poster_url = film.get('posterUrlPreview')
            if poster_url:
                try:
                    await update.message.reply_photo(
                        photo=poster_url,
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

        # Если есть больше результатов
        if len(films) > 3:
            await update.message.reply_text(
                f"Найдено фильмов: {len(films)}\n"
                "Показаны первые 3 результата.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        await update.message.reply_text(
            "❌ Ошибка при поиске.\n"
            "Попробуйте позже или другой запрос."
        )

async def search_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str = None):
    """Поиск фильмов по жанру"""
    if not genre:
        await update.message.reply_text("Укажите жанр: /genres драма")
        return

    # Получаем ID жанра
    genre_id = GENRE_MAP.get(genre.lower())
    if not genre_id:
        await update.message.reply_text(f"Жанр «{genre}» не найден.")
        return

    await update.message.reply_text(f"🎭 Ищу *{genre}*...", parse_mode='Markdown')

    try:
        result = api_client.get_films_by_filters(genre_id=genre_id, rating_from=7)
        films = result.get('items', [])[:5]

        if not films:
            await update.message.reply_text(f"По жанру «{genre}» ничего не найдено.")
            return

        text = f"🎭 *Лучшие фильмы в жанре {genre}:*\n\n"
        for i, film in enumerate(films, 1):
            title = film.get('nameRu') or 'Без названия'
            year = film.get('year', '')
            rating = film.get('ratingKinopoisk', '')

            text += f"{i}. *{title}*"
            if year:
                text += f" ({year})"
            if rating:
                text += f" ⭐ {rating}"
            text += "\n"

        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка поиска по жанру: {e}")
        await update.message.reply_text("❌ Ошибка при поиске по жанру.")

async def show_top250(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать топ-250 фильмов"""
    await update.message.reply_text("⭐ Загружаю топ-250 фильмов...")

    try:
        result = api_client.get_top_films(page=1)
        films = result.get('films', [])[:10]

        if not films:
            await update.message.reply_text("Не удалось загрузить топ фильмов.")
            return

        text = "⭐ *Топ-10 лучших фильмов:*\n\n"
        for i, film in enumerate(films, 1):
            title = film.get('nameRu') or 'Без названия'
            year = film.get('year', '')
            rating = film.get('rating', '')

            text += f"{i}. *{title}*"
            if year:
                text += f" ({year})"
            if rating:
                text += f" ⭐ {rating}"
            text += "\n"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка загрузки топа: {e}")
        await update.message.reply_text("❌ Не удалось загрузить топ фильмов.")

async def random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайный фильм"""
    # Фиктивные данные для теста
    movies = [
        {"title": "Начало", "year": "2010", "rating": "8.7", "genre": "фантастика, триллер", "desc": "Воры внедряются в сны, чтобы украсть идеи."},
        {"title": "Зеленая миля", "year": "1999", "rating": "9.1", "genre": "драма, фэнтези", "desc": "История надзирателя в тюрьме для смертников."},
        {"title": "Форрест Гамп", "year": "1994", "rating": "8.8", "genre": "драма, мелодрама", "desc": "Жизнь человека с низким IQ, который стал свидетелем ключевых событий истории."},
        {"title": "Поймай меня, если сможешь", "year": "2002", "rating": "8.1", "genre": "криминал, драма", "desc": "Подросток-аферист выдает себя за пилота, врача и юриста."},
        {"title": "Побег из Шоушенка", "year": "1994", "rating": "9.1", "genre": "драма", "desc": "Бухгалтер Энди Дюфрейн оказывается в тюрьме на пожизненный срок."},
    ]

    import random
    movie = random.choice(movies)

    text = f"🎲 *Случайный фильм для тебя:*\n\n"
    text += f"🎬 *{movie['title']}* ({movie['year']})\n"
    text += f"⭐ Рейтинг: {movie['rating']}/10\n"
    text += f"🎭 Жанр: {movie['genre']}\n"
    text += f"📝 {movie['desc']}\n\n"
    text += "Хочешь посмотреть?"

    keyboard = [[
        InlineKeyboardButton("🔍 Найти похожие", callback_data=f"similar_{movie['title']}"),
        InlineKeyboardButton("🎲 Другой фильм", callback_data="random_another")
    ]]

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать watchlist"""
    if not db_manager:
        await update.message.reply_text(
            "📋 *Мой Watchlist*\n\n"
            "База данных не настроена.\n\n"
            "Чтобы сохранять фильмы:\n"
            "1. Настройте базу данных\n"
            "2. Используйте кнопку «💾 В Watchlist» в результатах поиска",
            parse_mode='Markdown'
        )
        return

    user_id = update.effective_user.id

    try:
        watchlist = db_manager.get_watchlist(user_id)

        if not watchlist:
            await update.message.reply_text(
                "📭 *Твой Watchlist пуст!*\n\n"
                "Чтобы добавить фильмы:\n"
                "1. Найди фильм через поиск\n"
                "2. Нажми «💾 В Watchlist»\n\n"
                "Все сохраненные фильмы появятся здесь!",
                parse_mode='Markdown'
            )
            return

        text = "📋 *Твой Watchlist:*\n\n"
        for i, item in enumerate(watchlist[:5], 1):
            text += f"{i}. *{item['title']}*"
            if item.get('year'):
                text += f" ({item['year']})"
            text += "\n"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения watchlist: {e}")
        await update.message.reply_text("❌ Ошибка при загрузке Watchlist.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('info_'):
        # Информация о фильме
        film_id = data.split('_')[1]
        await show_film_info(query, context, film_id)

    elif data.startswith('similar_'):
        # Похожие фильмы
        film_id = data.split('_')[1]
        await show_similar_films(query, context, film_id)

    elif data == "random_another":
        # Еще случайный фильм
        await random_movie(query, context)

    else:
        await query.edit_message_text(f"Действие: {data}")

async def show_film_info(query, context, film_id: str):
    """Показать информацию о фильме"""
    try:
        if film_id.isdigit():
            film = api_client.get_film_details(int(film_id))
            if film:
                title = film.get('nameRu') or film.get('nameOriginal', 'Без названия')
                year = film.get('year', '')
                rating = film.get('ratingKinopoisk', '')
                description = film.get('description', '')

                text = f"🎬 *{title}*\n"
                if year:
                    text += f"📅 Год: {year}\n"
                if rating:
                    text += f"⭐ Рейтинг: {rating}\n"
                if description:
                    text += f"\n📝 {description}"

                await query.edit_message_text(text, parse_mode='Markdown')
                return

        await query.edit_message_text("❌ Не удалось загрузить информацию о фильме.")

    except Exception as e:
        logger.error(f"Ошибка получения информации о фильме: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке информации.")

async def show_similar_films(query, context, film_id: str):
    """Показать похожие фильмы"""
    try:
        if film_id.isdigit():
            similar = api_client.get_similar_films(int(film_id))
            if similar:
                text = "🎯 *Похожие фильмы:*\n\n"
                for i, film in enumerate(similar[:5], 1):
                    title = film.get('nameRu') or film.get('nameOriginal', 'Без названия')
                    text += f"{i}. {title}\n"

                await query.edit_message_text(text, parse_mode='Markdown')
                return

        await query.edit_message_text("😔 Не нашёл похожих фильмов.")

    except Exception as e:
        logger.error(f"Ошибка получения похожих фильмов: {e}")
        await query.edit_message_text("❌ Ошибка при поиске похожих фильмов.")