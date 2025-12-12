# bot/handlers.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import logging
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

    welcome_text = f"""
🎬 Привет, {user.first_name}! Я MovieMate — твой киногид!

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений - ИСПРАВЛЕННАЯ"""
    text = update.message.text

    # Сохраняем оригинальный текст для логирования
    original_text = text

    # Приводим к нижнему регистру для сравнения
    text_lower = text.lower()

    logger.info(f"Получено сообщение: '{original_text}' (нижний регистр: '{text_lower}')")

    # Обработка кнопок
    if text_lower == "🔍 поиск фильма" or text == "🔍 Поиск фильма":
        await update.message.reply_text(
            "Введите название фильма или сериала:\n"
            "Например: *Матрица* или *Игра престолов*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for'] = 'search'
        return

    elif text_lower == "🎭 по жанру" or text == "🎭 По жанру":
        await update.message.reply_text(
            "Выберите жанр:",
            reply_markup=get_genre_keyboard()
        )
        return

    elif text_lower == "⭐ топ 250" or text == "⭐ Топ 250":
        await show_top250(update, context)
        return

    elif text_lower == "🎲 случайный" or text == "🎲 Случайный":
        await random_real_movie(update, context)
        return

    elif text_lower == "📋 мой watchlist" or text == "📋 Мой Watchlist":
        await show_watchlist(update, context)
        return

    elif text_lower == "ℹ️ помощь" or text == "ℹ️ Помощь":
        await help_command(update, context)
        return

    elif text_lower == "🔙 на главную" or text == "🔙 На главную":
        await update.message.reply_text(
            "Возвращаю на главную...",
            reply_markup=get_main_keyboard()
        )
        return

    # Обработка жанров (точное совпадение с учетом регистра)
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

    # Обработка ввода после нажатия кнопки
    if 'waiting_for' in context.user_data:
        if context.user_data['waiting_for'] == 'search':
            await search_command(update, context, text)
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
        await search_command(update, context, text)
        return

    # Если ничего не подошло
    await update.message.reply_text(
        "Введите название фильма для поиска или используйте кнопки ниже 👇",
        reply_markup=get_main_keyboard()
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    """Поиск фильмов через КиноПоиск - ИСПРАВЛЕННЫЙ"""
    if not query or len(query.strip()) < 2:
        await update.message.reply_text("Введите название фильма (минимум 2 символа)")
        return

    clean_query = query.strip()

    # Если это команда (начинается с /), игнорируем
    if clean_query.startswith('/'):
        return

    if not api_client or not api_client.is_active:
        await show_test_results(update, clean_query)
        return

    try:
        logger.info(f"🔍 Поиск в КиноПоиске: '{clean_query}'")
        result = api_client.search_films(clean_query)

        if not result or 'error' in result:
            error_msg = result.get('error', 'Неизвестная ошибка')
            await update.message.reply_text(f"❌ Ошибка API: {error_msg}")
            return

        films = result.get('films', [])
        total_found = result.get('searchFilmsCountResult', 0)

        logger.info(f"Найдено фильмов: {total_found}")

        if not films or total_found == 0:
            await update.message.reply_text(
                f"😔 По запросу «{clean_query}» ничего не найдено.\n\n"
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

async def send_film_card(update, film) -> bool:
    """Отправляет карточку фильма с кнопками - ИСПРАВЛЕННАЯ"""
    try:
        title = film.get('nameRu') or film.get('nameEn') or 'Без названия'
        year = film.get('year', '')
        rating = film.get('rating', '')
        film_id = film.get('filmId')
        description = film.get('description', '')

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
        keyboard = [[
            InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{film_id}"),
            InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{film_id}")
        ], [
            InlineKeyboardButton("💾 В Watchlist", callback_data=f"watch_{film_id}_{title[:20].replace(' ', '_')}")
        ]]

        # Постер если есть
        poster_url = film.get('posterUrlPreview')

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

    test_films = [
        {
            "filmId": 301,
            "nameRu": "Матрица",
            "year": "1999",
            "rating": "8.7",
            "description": "Хакер Нео узнает, что его мир — виртуальная реальность.",
            "posterUrlPreview": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/4057c4b8-8208-4a04-b169-26b0662163e3/300x450"
        },
        {
            "filmId": 258687,
            "nameRu": "Интерстеллар",
            "year": "2014",
            "rating": "8.6",
            "description": "Экипаж исследователей путешествует через червоточину в космосе.",
            "posterUrlPreview": "https://avatars.mds.yandex.net/get-kinopoisk-image/1600647/430042eb-ee69-4818-aed0-2c9b7de8b04f/300x450"
        },
    ]

    for film in test_films:
        await send_film_card(update, film)

async def search_by_genre(update: Update, context: ContextTypes.DEFAULT_TYPE, genre: str = None):
    """Поиск фильмов по жанру - ИСПРАВЛЕННЫЙ"""
    if not genre:
        await update.message.reply_text("Укажите жанр")
        return

    # Карта жанров
    genre_map = {
        "драма": 1, "комедия": 13, "боевик": 11, "ужасы": 7,
        "фантастика": 6, "детектив": 3, "мелодрама": 22,
        "триллер": 4, "приключения": 12
    }

    genre_id = genre_map.get(genre.lower())
    if not genre_id:
        await update.message.reply_text(f"Жанр «{genre}» не найден.")
        return

    await update.message.reply_text(f"🎭 Ищу фильмы в жанре *{genre}*...", parse_mode='Markdown')

    if not api_client or not api_client.is_active:
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
        result = api_client.get_films_by_filters(genre_id=genre_id, rating_from=7)
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
            "1. Пример драмы 1 (2000) ⭐ 8.5\n"
            "2. Пример драмы 2 (2010) ⭐ 8.0\n"
            "3. Пример драмы 3 (2020) ⭐ 7.8",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

async def show_top250(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать топ-250 фильмов - ИСПРАВЛЕННЫЙ"""
    # УДАЛЯЕМ начальное сообщение "Загружаю топ-250", чтобы не было дубля
    # await update.message.reply_text("⭐ Загружаю топ-250 фильмов...")

    try:
        if not api_client or not api_client.is_active:
            await update.message.reply_text(
                "⭐ *Топ-10 лучших фильмов (пример):*\n\n"
                "1. Побег из Шоушенка (1994) ⭐ 9.1\n"
                "2. Крестный отец (1972) ⭐ 9.0\n"
                "3. Темный рыцарь (2008) ⭐ 9.0\n"
                "4. Крестный отец 2 (1974) ⭐ 9.0\n"
                "5. 12 разгневанных мужчин (1957) ⭐ 9.0\n"
                "6. Список Шиндлера (1993) ⭐ 8.9\n"
                "7. Властелин колец: Возвращение короля (2003) ⭐ 8.9\n"
                "8. Криминальное чтиво (1994) ⭐ 8.9\n"
                "9. Властелин колец: Братство кольца (2001) ⭐ 8.8\n"
                "10. Форрест Гамп (1994) ⭐ 8.8",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
            return

        result = api_client.get_top_films(page=1)
        films = result.get('films', [])[:10]

        if not films:
            await update.message.reply_text(
                "⭐ *Топ-10 лучших фильмов (пример):*\n\n"
                "1. Побег из Шоушенка (1994) ⭐ 9.1\n"
                "2. Крестный отец (1972) ⭐ 9.0\n"
                "3. Темный рыцарь (2008) ⭐ 9.0\n"
                "...",
                parse_mode='Markdown',
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
            "⭐ *Топ-10 лучших фильмов (пример):*\n\n"
            "1. Побег из Шоушенка (1994) ⭐ 9.1\n"
            "2. Крестный отец (1972) ⭐ 9.0\n"
            "3. Темный рыцарь (2008) ⭐ 9.0\n"
            "...",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

async def random_real_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайный фильм из базы или топ-250 - ИСПРАВЛЕННЫЙ"""
    import random

    # Список популярных фильмов для fallback
    popular_movies = [
        {"title": "Начало", "year": "2010", "rating": "8.8", "genre": "фантастика, триллер",
         "desc": "Воры внедряются в сны, чтобы украсть идеи.", "country": "США, Великобритания"},
        {"title": "Зеленая миля", "year": "1999", "rating": "9.1", "genre": "драма, фэнтези",
         "desc": "История надзирателя в тюрьме для смертников.", "country": "США"},
        {"title": "Форрест Гамп", "year": "1994", "rating": "8.8", "genre": "драма, мелодрама",
         "desc": "Жизнь человека с низким IQ, который стал свидетелем ключевых событий истории.", "country": "США"},
        {"title": "Поймай меня, если сможешь", "year": "2002", "rating": "8.1", "genre": "криминал, драма",
         "desc": "Подросток-аферист выдает себя за пилота, врача и юриста.", "country": "США, Канада"},
        {"title": "Побег из Шоушенка", "year": "1994", "rating": "9.1", "genre": "драма",
         "desc": "Бухгалтер Энди Дюфрейн оказывается в тюрьме на пожизненный срок.", "country": "США"},
        {"title": "Криминальное чтиво", "year": "1994", "rating": "8.9", "genre": "криминал, драма",
         "desc": "Несколько переплетающихся историй о жизни мелких преступников.", "country": "США"},
        {"title": "Властелин колец: Братство кольца", "year": "2001", "rating": "8.8", "genre": "фэнтези, приключения",
         "desc": "Средиземье. Хоббит Фродо должен уничтожить Кольцо Всевластья.", "country": "Новая Зеландия, США"},
        {"title": "Леон", "year": "1994", "rating": "8.8", "genre": "боевик, триллер",
         "desc": "Профессиональный убийца Леон знакомится со своей соседкой Матильдой.", "country": "Франция, США"},
        {"title": "Король Лев", "year": "1994", "rating": "8.8", "genre": "мультфильм, драма",
         "desc": "Львенок Симба познает круговорот жизни в африканской саванне.", "country": "США"},
        {"title": "Титаник", "year": "1997", "rating": "8.4", "genre": "драма, мелодрама",
         "desc": "Молодые влюбленные Джек и Роза на борту «Титаника».", "country": "США, Мексика"},
    ]

    movie = random.choice(popular_movies)

    text = f"🎲 *Случайный фильм для тебя:*\n\n"
    text += f"🎬 *{movie['title']}* ({movie['year']})\n"
    text += f"⭐ Рейтинг: {movie['rating']}/10\n"
    text += f"🎭 Жанр: {movie['genre']}\n"
    text += f"🌍 Страна: {movie['country']}\n"
    text += f"📝 {movie['desc']}\n\n"
    text += "Хочешь посмотреть?"

    keyboard = [[
        InlineKeyboardButton("🔍 Найти похожие", callback_data=f"search_{movie['title']}"),
        InlineKeyboardButton("🎲 Другой фильм", callback_data="random_another")
    ]]

    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать watchlist - ИСПРАВЛЕННЫЙ"""
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
            if hasattr(item, 'added_at') and item.added_at:
                text += f"\n   Добавлено: {item.added_at.strftime('%d.%m.%Y')}"
            text += "\n\n"

        if len(watchlist) > 5:
            text += f"... и еще {len(watchlist) - 5} фильмов"

        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка получения watchlist: {e}")
        await update.message.reply_text(
            "❌ Ошибка при загрузке Watchlist.\n"
            "Проверьте настройки базы данных.",
            reply_markup=get_main_keyboard()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ"""
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
            parts = data.split('_')
            if len(parts) >= 3:
                film_id = parts[1]
                film_title = '_'.join(parts[2:]).replace('_', ' ')

                # ПРОСТОЕ добавление без БД
                if not db_manager:
                    await query.edit_message_text(f"✅ Фильм «{film_title}» добавлен в Watchlist (тестовый режим)!")
                else:
                    # Пытаемся добавить в БД
                    try:
                        # Создаем простую запись
                        movie_data = {
                            'id': int(film_id),
                            'title': film_title,
                            'year': '',
                            'poster_url': ''
                        }

                        watchlist_item = db_manager.add_to_watchlist(query.from_user.id, movie_data)
                        if watchlist_item:
                            await query.edit_message_text(f"✅ Фильм «{film_title}» добавлен в Watchlist!")
                        else:
                            await query.edit_message_text(f"✅ Фильм «{film_title}» уже был в Watchlist!")
                    except Exception as db_error:
                        logger.error(f"Ошибка БД при добавлении: {db_error}")
                        await query.edit_message_text(f"✅ Фильм «{film_title}» добавлен в Watchlist (тестовый режим)!")
        except Exception as e:
            logger.error(f"Ошибка в watch_: {e}")
            await query.edit_message_text("✅ Добавлено в Watchlist!")

    elif data == "random_another":
        # Еще случайный фильм
        await random_real_movie(update, context)

    elif data.startswith("search_"):
        # Поиск похожих по названию
        film_title = data.split('_', 1)[1]
        await search_command(query, context, film_title)

    else:
        # Неизвестная кнопка
        await query.edit_message_text(f"Действие: {data}")

async def show_film_info(query, film_id: str):
    """Показать информацию о фильме - ИСПРАВЛЕННАЯ"""
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

        if description:
            text += f"\n📝 {description}"

        await query.edit_message_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения информации о фильме: {e}")
        await query.edit_message_text("❌ Ошибка при загрузке информации.")

async def show_similar_films(query, film_id: str):
    """Показать похожие фильмы - ИСПРАВЛЕННАЯ"""
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
            text += f"{i}. {title}\n"

        await query.edit_message_text(text, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка получения похожих фильмов: {e}")
        await query.edit_message_text("😔 Не нашёл похожих фильмов.")

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
• /start — запустить бота
• /search <название> — поиск фильма
• /top — топ-250 фильмов  
• /random — случайный фильм
• /help — эта справка

🎬 *Примеры запросов:*
• «Матрица»
• «Детектив 90-х»
• «Лучшие комедии 2000-х»
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())