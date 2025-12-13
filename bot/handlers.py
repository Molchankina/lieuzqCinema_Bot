# bot/handlers.py - ПОЛНЫЙ ИСПРАВЛЕННЫЙ КОД

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
    "криминал": 8
}

# Список популярных фильмов для случайного выбора (запасной вариант)
POPULAR_MOVIES = [
    {
        "id": 301,
        "title": "Матрица",
        "year": "1999",
        "rating": "8.7",
        "genre": "фантастика, триллер",
        "desc": "Хакер Нео узнает, что его мир — виртуальная реальность.",
        "country": "США, Австралия",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/4057c4b8-8208-4a04-b169-26b0662163e3/300x450"
    },
    {
        "id": 258687,
        "title": "Интерстеллар",
        "year": "2014",
        "rating": "8.6",
        "genre": "фантастика, драма",
        "desc": "Экипаж исследователей путешествует через червоточину в космосе.",
        "country": "США, Великобритания",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1600647/430042eb-ee69-4818-aed0-2c9b7de8b04f/300x450"
    },
    {
        "id": 435,
        "title": "Зеленая миля",
        "year": "1999",
        "rating": "9.1",
        "genre": "драма, фэнтези",
        "desc": "История надзирателя в тюрьме для смертников.",
        "country": "США",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/0b76b2a2-d1c7-4f04-a284-80ff7bb709a4/300x450"
    },
    {
        "id": 448,
        "title": "Форрест Гамп",
        "year": "1994",
        "rating": "8.8",
        "genre": "драма, мелодрама",
        "desc": "Жизнь человека с низким IQ, который стал свидетелем ключевых событий истории.",
        "country": "США",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/3560b757-9b95-45ec-af8c-623972370f9d/300x450"
    }
]

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

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    welcome_text = f"""
🎬 Привет, {user.first_name}! Я КиноПроводник — твой киногид!

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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📚 *КиноПроводник Bot — помощник по фильмам*

🎯 *Основные функции:*
• Поиск фильмов и сериалов
• Топ-250 лучших фильмов
• Подбор по жанрам
• Случайные рекомендации
• Список «Посмотреть позже»

⌨️ *Используй кнопки или команды:*
• /start — запустить бота
• /search <название> — поиск фильма
• /top — топ-250 фильмов  
• /random — случайный фильм
• /watchlist — мой список
• /help — эта справка

🎬 *Примеры запросов:*
• «Матрица»
• «Детектив 90-х»
• «Лучшие комедии 2000-х»
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /search"""
    query = ' '.join(context.args) if context.args else ''

    if not query:
        await update.message.reply_text(
            "Введите название фильма или сериала:\n"
            "Например: *Матрица* или *Игра престолов*",
            parse_mode='Markdown'
        )
        return

    await execute_search(update, query)

async def execute_search(update, query: str):
    """Выполнение поиска фильмов"""
    if not api_client or not api_client.is_active:
        await show_test_results(update, query)
        return

    try:
        logger.info(f"🔍 Поиск в КиноПоиске: '{query}'")
        result = api_client.search_films(query)

        if not result or 'error' in result:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await update.message.reply_text(f"❌ Ошибка API: {error_msg}")
            return

        films = result.get('films', [])
        total_found = result.get('searchFilmsCountResult', 0)

        logger.info(f"Найдено фильмов: {total_found}")

        if not films or total_found == 0:
            await update.message.reply_text(
                f"😔 По запросу «{query}» ничего не найдено.\n\n"
                "Попробуйте:\n"
                "• Уточнить название\n"
                "• Использовать русское название\n"
                "• Проверить орфографию"
            )
            return

        # Показываем первые 3 результата
        shown_count = 0
        for film in films[:3]:
            if await send_film_card(update, film):
                shown_count += 1

        if shown_count == 0:
            await update.message.reply_text("😔 Не удалось показать результаты. Попробуйте другой запрос.")

        # Если есть больше результатов
        if total_found > 3:
            await update.message.reply_text(
                f"📊 Найдено фильмов: {total_found}\n"
                f"Показаны первые {min(3, len(films))} результата.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка поиска: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при поиске.\n"
            "Попробуйте позже или другой запрос."
        )

async def send_film_card(update, film, from_watchlist: bool = False) -> bool:
    """Отправляет карточку фильма с кнопками"""
    try:
        title = film.get('nameRu') or film.get('nameEn') or film.get('title') or 'Без названия'
        year = film.get('year', '') or film.get('release_date', '')[:4]
        rating = film.get('rating', '') or film.get('ratingKinopoisk', '')
        film_id = film.get('filmId') or film.get('id')
        description = film.get('description', '') or film.get('overview', '')
        poster_url = film.get('posterUrlPreview') or film.get('poster_url')

        if not film_id:
            logger.error(f"Нет filmId для фильма: {title}")
            return False

        # Формируем текст
        text = f"*{title}*"
        if year:
            text += f" ({year})"

        if rating:
            text += f"\n⭐ Рейтинг: {rating}"

        if description:
            text += f"\n\n{description[:150]}..."

        # Кнопки действий
        keyboard = []

        if from_watchlist:
            # Для watchlist добавляем кнопку удаления
            keyboard.append([
                InlineKeyboardButton("🗑️ Удалить из Watchlist", callback_data=f"remove_{film_id}")
            ])
        else:
            # Обычные кнопки для поиска
            keyboard.append([
                InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{film_id}"),
                InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{film_id}")
            ])

            if not from_watchlist:
                keyboard.append([
                    InlineKeyboardButton("💾 В Watchlist", callback_data=f"watch_{film_id}")
                ])

        try:
            if poster_url and poster_url.startswith('http'):
                await update.message.reply_photo(
                    photo=poster_url,
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки карточки: {e}")
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return True

    except Exception as e:
        logger.error(f"Ошибка формирования карточки: {e}")
        return False

async def show_test_results(update, query):
    """Показать тестовые результаты (когда API не работает)"""
    logger.info(f"🔍 Тестовый поиск: '{query}'")

    for film in POPULAR_MOVIES[:2]:
        await send_film_card(update, film)

async def show_top250(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /top - показывает топ-250 фильмов"""
    if not api_client or not api_client.is_active:
        # Тестовые данные
        text = "⭐ *Топ-10 лучших фильмов (пример):*\n\n"
        text += "1. *Побег из Шоушенка* (1994) ⭐ 9.1\n"
        text += "2. *Крестный отец* (1972) ⭐ 9.0\n"
        text += "3. *Темный рыцарь* (2008) ⭐ 9.0\n"
        text += "4. *Крестный отец 2* (1974) ⭐ 9.0\n"
        text += "5. *12 разгневанных мужчин* (1957) ⭐ 9.0\n"
        text += "6. *Список Шиндлера* (1993) ⭐ 8.9\n"
        text += "7. *Властелин колец: Возвращение короля* (2003) ⭐ 8.9\n"
        text += "8. *Криминальное чтиво* (1994) ⭐ 8.9\n"
        text += "9. *Властелин колец: Братство кольца* (2001) ⭐ 8.8\n"
        text += "10. *Форрест Гамп* (1994) ⭐ 8.8"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    try:
        result = api_client.get_top_films(page=1)
        films = result.get('films', [])[:10]

        if not films:
            await update.message.reply_text(
                "Не удалось загрузить топ фильмов. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
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
        await update.message.reply_text(
            "❌ Не удалось загрузить топ фильмов. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

async def get_random_movie_from_api() -> dict:
    """Получить случайный фильм из КиноПоиска с рейтингом не ниже 8.5"""
    if not api_client or not api_client.is_active:
        return random.choice(POPULAR_MOVIES)

    try:
        # Ищем фильмы с рейтингом от 8.5
        result = api_client.get_films_by_filters(rating_from=85)  # 85 = 8.5 в API

        if result and 'items' in result and result['items']:
            items = result['items']

            # Фильтруем фильмы с рейтингом от 8.5
            good_movies = []
            for film in items:
                rating_str = film.get('ratingKinopoisk', '0')
                try:
                    rating = float(rating_str) if rating_str else 0
                    if rating >= 8.5:
                        good_movies.append(film)
                except (ValueError, TypeError):
                    continue

            if good_movies:
                return random.choice(good_movies)

        # Если не нашли по фильтрам, берем из топа
        result = api_client.get_top_films(page=random.randint(1, 10))
        if result and 'films' in result and result['films']:
            films = result['films']
            good_films = []
            for film in films:
                rating_str = film.get('rating', '0')
                try:
                    rating = float(rating_str) if rating_str else 0
                    if rating >= 8.5:
                        good_films.append(film)
                except (ValueError, TypeError):
                    continue

            if good_films:
                return random.choice(good_films)

        # Если ничего не нашлось, берем любой фильм из топа
        if result and 'films' in result and result['films']:
            return random.choice(result['films'])

    except Exception as e:
        logger.error(f"Ошибка получения случайного фильма: {e}")

    # Возвращаем случайный из локального списка
    return random.choice(POPULAR_MOVIES)

async def random_real_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /random - случайный фильм из КиноПоиска"""
    await update.message.reply_text("🎲 Ищу случайный фильм с рейтингом от 8.5...")

    try:
        movie = await get_random_movie_from_api()

        if movie:
            title = movie.get('nameRu') or movie.get('nameOriginal') or movie.get('title') or 'Неизвестный фильм'
            year = movie.get('year') or movie.get('release_date', '')[:4] or '?'
            rating = movie.get('rating') or movie.get('ratingKinopoisk') or '?'

            text = f"🎲 *Случайный фильм для тебя:*\n\n"
            text += f"🎬 *{title}* ({year})\n"
            text += f"⭐ Рейтинг: {rating}\n"

            # Пробуем получить детали для более полной информации
            film_id = movie.get('filmId') or movie.get('id')
            if film_id and api_client:
                details = api_client.get_film_details(film_id)
                if details:
                    genres = details.get('genres', [])
                    if genres:
                        genre_names = [g.get('genre', '') for g in genres[:3]]
                        text += f"🎭 Жанр: {', '.join(genre_names)}\n"

                    countries = details.get('countries', [])
                    if countries:
                        country_names = [c.get('country', '') for c in countries[:2]]
                        text += f"🌍 Страна: {', '.join(country_names)}\n"

                    description = details.get('description', '')
                    if description:
                        text += f"\n📝 {description[:200]}..."

            # Создаем карточку фильма
            await send_film_card(update, movie)

        else:
            await update.message.reply_text(
                "Не удалось найти случайный фильм. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка в random_real_movie: {e}")
        # Показываем локальный фильм как запасной вариант
        movie = random.choice(POPULAR_MOVIES)
        await send_film_card(update, movie)

async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /watchlist - показывает Watchlist"""
    if not db_manager:
        await update.message.reply_text(
            "📋 *Мой Watchlist*\n\n"
            "Для работы Watchlist необходимо:\n"
            "1. Настроить базу данных\n"
            "2. Добавить переменную DATABASE_URL в .env\n\n"
            "Сейчас используйте кнопку «💾 В Watchlist» для теста.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
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
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
            return

        text = "📋 *Твой Watchlist:*\n\n"
        for i, item in enumerate(watchlist[:5], 1):
            text += f"{i}. *{item['title']}*"
            if item.get('year'):
                text += f" ({item['year']})"
            if 'added_at' in item and item['added_at']:
                if hasattr(item['added_at'], 'strftime'):
                    text += f"\n   📅 Добавлено: {item['added_at'].strftime('%d.%m.%Y')}"
            text += "\n\n"

        if len(watchlist) > 5:
            text += f"... и еще {len(watchlist) - 5} фильмов"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Показываем карточки фильмов из watchlist с кнопкой удаления
        for item in watchlist[:3]:  # Показываем первые 3
            film_data = {
                'id': item['movie_id'],
                'title': item['title'],
                'year': item.get('year', ''),
                'poster_url': item.get('poster_url', '')
            }
            await send_film_card(update, film_data, from_watchlist=True)

    except Exception as e:
        logger.error(f"Ошибка получения watchlist: {e}")
        await update.message.reply_text(
            "❌ Ошибка при загрузке Watchlist.\n"
            "Проверьте настройки базы данных.",
            reply_markup=get_main_keyboard()
        )

# ==================== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений и кнопок быстрого действия"""
    text = update.message.text

    # Сохраняем оригинальный текст для логирования
    original_text = text

    # Приводим к нижнему регистру для сравнения
    text_lower = text.lower()

    logger.info(f"Получено сообщение: '{original_text}'")

    # Обработка кнопок быстрого действия
    if text == "🔍 Поиск фильма":
        await update.message.reply_text(
            "Введите название фильма или сериала:\nНапример: *Матрица* или *Игра престолов*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'search'
        return

    elif text == "🎭 По жанру":
        await update.message.reply_text(
            "Выберите жанр:",
            reply_markup=get_genre_keyboard()
        )
        return

    elif text == "⭐ Топ 250":
        await show_top250(update, context)
        return

    elif text == "🎲 Случайный":
        await random_real_movie(update, context)
        return

    elif text == "📋 Мой Watchlist":
        await show_watchlist(update, context)
        return

    elif text == "ℹ️ Помощь":
        await help_command(update, context)
        return

    elif text == "🔙 На главную":
        await update.message.reply_text(
            "Возвращаю на главную...",
            reply_markup=get_main_keyboard()
        )
        return

    # Обработка жанров
    genre_buttons = {
        "🎭 Драма": "драма",
        "😂 Комедия": "комедия",
        "🔫 Боевик": "боевик",
        "👻 Ужасы": "ужасы",
        "🚀 Фантастика": "фантастика",
        "🔍 Детектив": "детектив",
        "❤️ Мелодрама": "мелодрама",
        "🧩 Триллер": "триллер",
        "🎬 Приключения": "приключения"
    }

    if text in genre_buttons:
        genre = genre_buttons[text]
        await search_by_genre(update, context, genre)
        return

    # Обработка ввода после нажатия кнопки поиска
    if 'waiting_for' in context.user_data and context.user_data['waiting_for'] == 'search':
        await execute_search(update, text)
        context.user_data.pop('waiting_for', None)
        return

    # Если сообщение содержит только цифры (например, "250"), игнорируем
    if text.strip().isdigit() and len(text.strip()) <= 3:
        logger.info(f"Игнорируем числовой запрос: '{text}'")
        await update.message.reply_text(
            "Используйте кнопки ниже для навигации 👇",
            reply_markup=get_main_keyboard()
        )
        return

    # Прямые текстовые запросы (исключая команды)
    if text and len(text.strip()) > 2 and not text.strip().startswith('/'):
        await execute_search(update, text)
        return

    # Если ничего не подошло
    await update.message.reply_text(
        "Введите название фильма для поиска или используйте кнопки ниже 👇",
        reply_markup=get_main_keyboard()
    )

async def search_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str):
    """Поиск фильмов по жанру"""
    await update.message.reply_text(f"🎭 Ищу фильмы в жанре *{genre}*...", parse_mode='Markdown')

    if not api_client or not api_client.is_active:
        # Тестовые данные для жанра
        await update.message.reply_text(
            f"🎭 *Фильмы в жанре {genre}:*\n\n"
            "1. Пример фильма 1 (2000) ⭐ 8.5\n"
            "2. Пример фильма 2 (2010) ⭐ 8.0\n"
            "3. Пример фильма 3 (2020) ⭐ 7.8\n\n"
            "⚠️ API не активен, показаны примеры",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    try:
        genre_id = GENRE_MAP.get(genre.lower())
        if not genre_id:
            await update.message.reply_text(f"Жанр «{genre}» не найден в базе.")
            return

        result = api_client.get_films_by_filters(genre_id=genre_id, rating_from=70)
        films = result.get('items', [])[:5]

        if not films:
            await update.message.reply_text(
                f"По жанру «{genre}» ничего не найдено.\n"
                "Попробуйте другой жанр.",
                reply_markup=get_genre_keyboard()
            )
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

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка поиска по жанру: {e}")
        await update.message.reply_text(
            f"🎭 *Фильмы в жанре {genre}:*\n\n"
            "1. Пример фильма 1 (2000) ⭐ 8.5\n"
            "2. Пример фильма 2 (2010) ⭐ 8.0\n"
            "3. Пример фильма 3 (2020) ⭐ 7.8\n\n"
            "⚠️ Ошибка API, показаны примеры",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

# ==================== ОБРАБОТЧИК INLINE-КНОПОК ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Нажата inline-кнопка: {data}")

    if data.startswith('info_'):
        # Информация о фильме
        try:
            film_id = data.split('_')[1]
            await show_film_info(query, film_id)
        except Exception as e:
            logger.error(f"Ошибка в info_: {e}")
            await query.edit_message_text("❌ Не удалось загрузить информацию о фильме.")

    elif data.startswith('similar_'):
        # Похожие фильмы
        try:
            film_id = data.split('_')[1]
            await show_similar_films(query, film_id)
        except Exception as e:
            logger.error(f"Ошибка в similar_: {e}")
            await query.edit_message_text("😔 Не нашёл похожих фильмов.")

    elif data.startswith('watch_'):
        # Добавить в Watchlist
        try:
            film_id = data.split('_')[1]

            # Получаем информацию о фильме
            film_info = {}
            if api_client:
                film_info = api_client.get_film_details(int(film_id))

            # Создаем данные фильма
            movie_data = {
                'id': int(film_id),
                'title': film_info.get('nameRu') or 'Неизвестный фильм',
                'year': film_info.get('year', ''),
                'poster_url': film_info.get('posterUrl', '')
            }

            # Добавляем в watchlist
            if db_manager and db_manager.add_to_watchlist(query.from_user.id, movie_data):
                await query.edit_message_text(f"✅ Фильм «{movie_data['title']}» добавлен в Watchlist!")
            else:
                await query.edit_message_text(f"✅ Фильм «{movie_data['title']}» уже был в Watchlist или произошла ошибка!")

        except Exception as e:
            logger.error(f"Ошибка в watch_: {e}")
            await query.edit_message_text("❌ Ошибка при добавлении в Watchlist.")

    elif data.startswith('remove_'):
        # Удалить из Watchlist
        try:
            film_id = data.split('_')[1]

            if db_manager and db_manager.remove_from_watchlist(query.from_user.id, int(film_id)):
                await query.edit_message_text("✅ Фильм удален из Watchlist!")
            else:
                await query.edit_message_text("❌ Фильм не найден в Watchlist.")

        except Exception as e:
            logger.error(f"Ошибка в remove_: {e}")
            await query.edit_message_text("❌ Ошибка при удалении из Watchlist.")

    elif data == "random_another":
        # Еще случайный фильм
        await random_real_movie(update, context)

    elif data.startswith("search_"):
        # Поиск похожих по названию
        film_title = data.split('_', 1)[1]
        await execute_search(update, film_title)

    else:
        # Неизвестная кнопка
        await query.edit_message_text(f"Действие: {data}")

async def show_film_info(query, film_id: str):
    """Показать информацию о фильме"""
    try:
        if not api_client or not api_client.is_active:
            await query.edit_message_text(
                f"🎬 *Информация о фильме (ID: {film_id})*\n\n"
                "⚠️ API не активен\n"
                "Для получения информации настройте КиноПоиск API",
                parse_mode='Markdown'
            )
            return

        film = api_client.get_film_details(int(film_id))
        if not film:
            await query.edit_message_text("❌ Не удалось загрузить информацию о фильме.")
            return

        title = film.get('nameRu') or film.get('nameOriginal', 'Без названия')
        year = film.get('year', '')
        rating = film.get('ratingKinopoisk', '')
        description = film.get('description', '')

        text = f"🎬 *{title}*\n"
        if year:
            text += f"📅 Год: {year}\n"
        if rating:
            text += f"⭐ Рейтинг КиноПоиск: {rating}\n"

        # Жанры
        genres = film.get('genres', [])
        if genres:
            genre_names = [g.get('genre', '') for g in genres[:3]]
            text += f"🎭 Жанр: {', '.join(genre_names)}\n"

        # Страны
        countries = film.get('countries', [])
        if countries:
            country_names = [c.get('country', '') for c in countries[:2]]
            text += f"🌍 Страна: {', '.join(country_names)}\n"

        # Длительность
        film_length = film.get('filmLength')
        if film_length:
            text += f"⏱️ Длительность: {film_length} мин.\n"

        # Бюджет и сборы
        budget = film.get('budget')
        if budget:
            text += f"💰 Бюджет: ${budget:,}\n"

        if description:
            text += f"\n📝 {description}"

        await query.edit_message_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения информации о фильме: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке информации.")

async def show_similar_films(query, film_id: str):
    """Показать похожие фильмы"""
    try:
        if not api_client or not api_client.is_active:
            await query.edit_message_text(
                f"🎯 *Похожие фильмы (ID: {film_id})*\n\n"
                "1. Пример похожего фильма 1\n"
                "2. Пример похожего фильма 2\n"
                "3. Пример похожего фильма 3\n\n"
                "⚠️ API не активен, показаны примеры",
                parse_mode='Markdown'
            )
            return

        similar = api_client.get_similar_films(int(film_id))
        if not similar:
            await query.edit_message_text("😔 Не нашёл похожих фильмов.")
            return

        text = "🎯 *Похожие фильмы:*\n\n"
        for i, film in enumerate(similar[:5], 1):
            title = film.get('nameRu') or film.get('nameOriginal', 'Без названия')
            rating = film.get('ratingKinopoisk', '')

            text += f"{i}. *{title}*"
            if rating:
                text += f" ⭐ {rating}"
            text += "\n"

        await query.edit_message_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения похожих фильмов: {e}")
        await query.edit_message_text("😔 Не нашёл похожих фильмов.")