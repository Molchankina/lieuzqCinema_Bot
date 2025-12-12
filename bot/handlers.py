# bot/handlers.py - оптимизирован для КиноПоиска

import logging
import random
from telegram import InputMediaPhoto
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

    # Обработка кнопок
    if text == "🎲 случайный":
        # ПРЯМОЙ ВЫЗОВ реального случайного фильма
        await random_real_movie(update, context)

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
        # Режим тестовых данных
        await show_test_results(update, query)
        return

    await update.message.reply_text(f"🔍 Ищу: *{query}*...", parse_mode='Markdown')

    try:
        result = api_client.search_films(query)
        films = result.get('films', [])

        if not films:
            await update.message.reply_text(f"😔 По запросу «{query}» ничего не найдено.")
            return

        # Показываем первые 3 результата
        for i, film in enumerate(films[:3], 1):
            await send_film_card(update, film, i)

        # Если есть больше результатов
        if len(films) > 3:
            await update.message.reply_text(
                f"Найдено фильмов: {len(films)}\nПоказаны первые 3 результата.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        await show_test_results(update, query)  # Fallback на тестовые данные

async def send_film_card(update, film, index=1):
    """Отправляет карточку фильма с кнопками"""
    title = film.get('nameRu') or film.get('nameEn') or 'Без названия'
    year = film.get('year', '')
    rating = film.get('rating', '')
    film_id = film.get('filmId', 0)
    description = film.get('description', '')

    # Формируем текст
    text = f"*{title}*"
    if year:
        text += f" ({year})"

    if rating:
        text += f"\n⭐ Рейтинг: {rating}"

    if description:
        text += f"\n\n{description[:150]}..."

    # Подготавливаем данные для callback
    # Убираем специальные символы из названия для callback
    safe_title = ''.join(c for c in title if c.isalnum() or c in ' _').replace(' ', '_')

    # Кнопки действий
    keyboard = [[
        InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{film_id}"),
        InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{film_id}")
    ], [
        InlineKeyboardButton("💾 В Watchlist", callback_data=f"watch_{film_id}_{safe_title[:15]}")
    ]]

    # Постер если есть
    poster_url = film.get('posterUrlPreview')

    try:
        if poster_url and poster_url.startswith('http'):
            if isinstance(update, Update):
                await update.message.reply_photo(
                    photo=poster_url,
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.edit_media(
                    media=InputMediaPhoto(media=poster_url, caption=text, parse_mode='Markdown'),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            if isinstance(update, Update):
                await update.message.reply_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    except Exception as e:
        logger.error(f"Ошибка отправки карточки: {e}")
        if isinstance(update, Update):
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

async def show_test_results(update, query):
    """Показать тестовые результаты (когда API не работает)"""
    await update.message.reply_text(f"🔍 Тестовый поиск: *{query}*", parse_mode='Markdown')

    test_films = [
        {"filmId": 301, "nameRu": "Матрица", "year": "1999", "rating": "8.7",
         "description": "Хакер Нео узнает, что его мир — виртуальная реальность.",
         "posterUrlPreview": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/4057c4b8-8208-4a04-b169-26b0662163e3/300x450"},
        {"filmId": 258687, "nameRu": "Интерстеллар", "year": "2014", "rating": "8.6",
         "description": "Экипаж исследователей путешествует через червоточину в космосе.",
         "posterUrlPreview": "https://avatars.mds.yandex.net/get-kinopoisk-image/1600647/430042eb-ee69-4818-aed0-2c9b7de8b04f/300x450"},
        {"filmId": 447301, "nameRu": "Начало", "year": "2010", "rating": "8.8",
         "description": "Воры внедряются в сны, чтобы украсть идеи.",
         "posterUrlPreview": "https://avatars.mds.yandex.net/get-kinopoisk-image/1629390/8a16e5c4-7d49-46a9-9b4a-85c9f5c4674b/300x450"},
    ]

    for i, film in enumerate(test_films, 1):
        await send_film_card(update, film, i)
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
    await update.message.reply_text("⭐ Загружаю топ-10 фильмов...")

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

async def add_to_watchlist(query, film_id: str, film_title: str = ""):
    """Добавить фильм в Watchlist"""
    try:
        user_id = query.from_user.id

        # Проверяем, есть ли менеджер БД
        if not db_manager:
            await query.edit_message_text(
                "❌ База данных не настроена.\n\n"
                "Watchlist временно недоступен."
            )
            return

        # Если film_id - число, пытаемся получить информацию о фильме
        film_info = {}
        if film_id.isdigit() and api_client and api_client.is_active:
            try:
                film_info = api_client.get_film_details(int(film_id))
            except:
                pass

        # Создаем данные фильма для БД
        movie_data = {
            'id': int(film_id) if film_id.isdigit() else 0,
            'title': film_title or film_info.get('nameRu', 'Неизвестный фильм'),
            'original_title': film_info.get('nameOriginal', ''),
            'release_date': str(film_info.get('year', '')),
            'overview': film_info.get('description', ''),
            'poster_path': film_info.get('posterUrl', ''),
            'media_type': 'movie',
            'genres': str([g.get('genre', '') for g in film_info.get('genres', [])]),
            'vote_average': film_info.get('ratingKinopoisk', 0.0)
        }

        # Добавляем в БД
        result = db_manager.add_to_watchlist(user_id, movie_data)

        if result:
            # Обновляем сообщение с фильмом
            try:
                current_text = query.message.caption or query.message.text
                new_text = current_text + "\n\n✅ *Добавлено в Watchlist!*"

                # Сохраняем клавиатуру
                keyboard = query.message.reply_markup

                if query.message.photo:
                    await query.edit_message_caption(
                        caption=new_text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                else:
                    await query.edit_message_text(
                        text=new_text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )

                # Также отправляем отдельное подтверждение
                await query.message.reply_text(
                    f"🎬 Фильм «{movie_data['title']}» добавлен в ваш Watchlist!",
                    reply_markup=get_main_keyboard()
                )

            except Exception as e:
                logger.error(f"Ошибка обновления сообщения: {e}")
                await query.edit_message_text(
                    f"✅ Фильм «{movie_data['title']}» добавлен в Watchlist!"
                )
        else:
            await query.edit_message_text(
                f"🎬 Фильм «{movie_data['title']}» уже в вашем Watchlist!"
            )

    except Exception as e:
        logger.error(f"Ошибка добавления в Watchlist: {e}")
        await query.edit_message_text(
            "❌ Не удалось добавить в Watchlist.\n"
            "Возможно, фильм уже добавлен или произошла ошибка."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок - ИСПРАВЛЕННЫЙ"""
    query = update.callback_query
    await query.answer()

    data = query.data

    # Логируем что пришло
    logger.info(f"Нажата кнопка с data: {data}")

    if data.startswith('info_'):
        # Информация о фильме
        try:
            film_id = int(data.split('_')[1])
            await show_film_info(query, film_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга film_id: {e}, data: {data}")
            await query.edit_message_text("❌ Ошибка: неверный формат данных")

    elif data.startswith('similar_'):
        # Похожие фильмы
        try:
            film_id = int(data.split('_')[1])
            await show_similar_films(query, film_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка парсинга film_id для похожих: {e}")
            await query.edit_message_text("❌ Ошибка при поиске похожих")

    elif data.startswith('watch_'):
        try:
            parts = data.split('_')
            logger.info(f"Watchlist данные: {parts}")  # Отладка

            if len(parts) >= 3:
                film_id = parts[1]
                film_title = '_'.join(parts[2:])  # Название может содержать _

                # Проверяем film_id
                if not film_id.isdigit():
                    await query.edit_message_text("❌ Ошибка: неверный ID фильма")
                    return

                await query.answer("Добавляю в Watchlist...")
                await add_to_watchlist(query, film_id, film_title)
            else:
                await query.answer()
                await query.edit_message_text("✅ Добавлено в Watchlist!")

        except Exception as e:
            logger.error(f"Ошибка обработки watch кнопки: {e}")
            await query.answer("❌ Ошибка при добавлении")
            await query.edit_message_text("❌ Не удалось добавить в Watchlist")

    elif data == "random_another":
        # Еще случайный фильм
        await random_movie(update, context)

    elif data == "random_real":
        # Настоящий случайный фильм из топ-250
        await random_real_movie(update, context)

    else:
        await query.edit_message_text(f"Действие: {data}")

async def random_real_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайный фильм из топ-250 КиноПоиска"""
    if not api_client or not api_client.is_active:
        # Если API не работает, показываем тестовый
        await random_movie(update, context)
        return

    try:
        # Получаем случайную страницу из топ-250 (всего 13 страниц по 20 фильмов)
        import random
        page = random.randint(1, 13)

        await update.message.reply_text("🎲 Ищу случайный фильм из топ-250...")

        result = api_client.get_top_films(page=page)
        films = result.get('films', [])

        if not films:
            await update.message.reply_text("Не удалось загрузить топ фильмов.")
            await random_movie(update, context)  # Fallback на тестовый
            return

        # Выбираем случайный фильм со страницы
        film = random.choice(films)
        film_id = film.get('filmId')

        if film_id:
            # Получаем полную информацию
            film_details = api_client.get_film_details(film_id)
            if film_details:
                await send_random_film_card(update, film_details)
            else:
                await send_film_card(update, film)
        else:
            await send_film_card(update, film)

        # Кнопка для другого случайного фильма
        keyboard = [[
            InlineKeyboardButton("🎲 Другой случайный", callback_data="random_real"),
            InlineKeyboardButton("⭐ Топ-250", callback_data="show_top")
        ]]

        if isinstance(update, Update):
            await update.message.reply_text(
                "Хочешь еще один случайный фильм?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.edit_message_text(
                "Хочешь еще один случайный фильм?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        logger.error(f"Ошибка получения случайного фильма: {e}")
        await random_movie(update, context)  # Fallback на тестовый

async def send_random_film_card(update, film_details):
    """Отправляет карточку случайного фильма"""
    title = film_details.get('nameRu') or film_details.get('nameOriginal', 'Без названия')
    year = film_details.get('year', '')
    rating = film_details.get('ratingKinopoisk', '')
    description = film_details.get('description', '')
    film_id = film_details.get('kinopoiskId', '')

    # Формируем красивый текст
    text = "🎲 *Случайный фильм из топ-250!*\n\n"
    text += f"🎬 *{title}*"
    if year:
        text += f" ({year})"

    if rating:
        text += f"\n⭐ Рейтинг: {rating}/10"

    # Жанры
    genres = film_details.get('genres', [])
    if genres:
        genre_names = [g.get('genre', '') for g in genres[:3]]
        text += f"\n🎭 Жанр: {', '.join(genre_names)}"

    # Страны
    countries = film_details.get('countries', [])
    if countries:
        country_names = [c.get('country', '') for c in countries[:2]]
        text += f"\n🌍 Страна: {', '.join(country_names)}"

    # Описание
    if description:
        text += f"\n\n📝 {description[:200]}..."

    # Кнопки
    keyboard = [[
        InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{film_id}"),
        InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{film_id}")
    ], [
        InlineKeyboardButton("🎲 Другой случайный", callback_data="random_real"),
        InlineKeyboardButton("💾 В Watchlist", callback_data=f"watch_{film_id}_{title[:20]}")
    ]]

    # Постер
    poster_url = film_details.get('posterUrl') or film_details.get('posterUrlPreview')

    try:
        if isinstance(update, Update):
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
        else:
            # Если это callback query
            if poster_url and poster_url.startswith('http'):
                await update.message.edit_media(
                    media=InputMediaPhoto(media=poster_url, caption=text, parse_mode='Markdown'),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.edit_message_text(
                    text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    except Exception as e:
        logger.error(f"Ошибка отправки случайного фильма: {e}")
        if isinstance(update, Update):
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

async def random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовый случайный фильм (если API не работает)"""
    movies = [
        {
            "nameRu": "Начало", "year": "2010", "rating": "8.8",
            "description": "Воры внедряются в сны, чтобы украсть идеи.",
            "genres": [{"genre": "фантастика"}, {"genre": "триллер"}],
            "countries": [{"country": "США"}, {"country": "Великобритания"}]
        },
        {
            "nameRu": "Зеленая миля", "year": "1999", "rating": "9.1",
            "description": "История надзирателя в тюрьме для смертников.",
            "genres": [{"genre": "драма"}, {"genre": "фэнтези"}],
            "countries": [{"country": "США"}]
        },
        {
            "nameRu": "Форрест Гамп", "year": "1994", "rating": "8.8",
            "description": "Жизнь человека с низким IQ, который стал свидетелем ключевых событий истории.",
            "genres": [{"genre": "драма"}, {"genre": "мелодрама"}],
            "countries": [{"country": "США"}]
        },
    ]

    import random
    movie = random.choice(movies)

    text = "🎲 *Случайный фильм для тебя:*\n\n"
    text += f"🎬 *{movie['nameRu']}* ({movie['year']})\n"
    text += f"⭐ Рейтинг: {movie['rating']}/10\n"

    if movie.get('genres'):
        genre_names = [g.get('genre', '') for g in movie['genres']]
        text += f"🎭 Жанр: {', '.join(genre_names)}\n"

    if movie.get('countries'):
        country_names = [c.get('country', '') for c in movie['countries']]
        text += f"🌍 Страна: {', '.join(country_names)}\n"

    text += f"📝 {movie['description']}\n\n"
    text += "Хочешь посмотреть?"

    keyboard = [[
        InlineKeyboardButton("🎲 Настоящий случайный", callback_data="random_real"),
        InlineKeyboardButton("🎲 Еще тестовый", callback_data="random_another")
    ]]

    if isinstance(update, Update):
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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