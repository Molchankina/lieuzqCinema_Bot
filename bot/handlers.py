# bot/handlers.py - ОБНОВЛЕННЫЙ БЕЗ КНОПОК "ПОДРОБНЕЕ" И "ПОХОЖИЕ"

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
        "filmId": 301,
        "title": "Матрица",
        "year": "1999",
        "rating": "8.7",
        "genre": "фантастика, триллер",
        "desc": "Хакер Нео узнает, что его мир — виртуальная реальность, созданная машинами для порабощения человечества. Вместе с группой повстанцев он должен сразиться с системой и освободить людей.",
        "country": "США, Австралия",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/4057c4b8-8208-4a04-b169-26b0662163e3/300x450"
    },
    {
        "id": 258687,
        "filmId": 258687,
        "title": "Интерстеллар",
        "year": "2014",
        "rating": "8.6",
        "genre": "фантастика, драма",
        "desc": "Когда засуха приводит человечество к продовольственному кризису, коллектив исследователей и учёных отправляется сквозь червоточину в путешествие, чтобы превзойти прежние ограничения для космических путешествий человека и переселить человечество на другую планету.",
        "country": "США, Великобритания",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1600647/430042eb-ee69-4818-aed0-2c9b7de8b04f/300x450"
    },
    {
        "id": 435,
        "filmId": 435,
        "title": "Зеленая миля",
        "year": "1999",
        "rating": "9.1",
        "genre": "драма, фэнтези",
        "desc": "Пол Эджкомб — начальник блока смертников в тюрьме «Холодная гора». В его блок поступает Джон Коффи, осужденный за убийство двух маленьких девочек. Но вскоре Пол понимает, что перед ним не обычный преступник, а человек с невероятными способностями.",
        "country": "США",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/0b76b2a2-d1c7-4f04-a284-80ff7bb709a4/300x450"
    },
    {
        "id": 448,
        "filmId": 448,
        "title": "Форрест Гамп",
        "year": "1994",
        "rating": "8.8",
        "genre": "драма, мелодрама",
        "desc": "От лица главного героя Форреста Гампа, слабоумного безобидного человека с благородным и открытым сердцем, рассказывается история его необыкновенной жизни. Он стал свидетелем ключевых событий истории Америки второй половины XX века.",
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def extract_film_id(film_data: dict) -> int:
    """Извлечь ID фильма из данных (обрабатывает разные форматы)"""
    # Пробуем разные возможные ключи для ID
    film_id = film_data.get('filmId') or film_data.get('kinopoiskId') or film_data.get('id')

    # Если это строка, пытаемся преобразовать в число
    if isinstance(film_id, str):
        try:
            return int(film_id)
        except (ValueError, TypeError):
            # Пробуем извлечь из других полей
            pass

    # Если все еще нет ID, используем заглушку
    if not film_id:
        film_id = film_data.get('nameRu', 'unknown').replace(' ', '_')

    return film_id

def get_film_title(film_data: dict) -> str:
    """Получить название фильма"""
    return film_data.get('nameRu') or film_data.get('nameEn') or film_data.get('title') or 'Без названия'

async def send_film_card(update, film, from_watchlist: bool = False) -> bool:
    """Отправляет карточку фильма с кнопками"""
    try:
        title = get_film_title(film)
        year = film.get('year', '') or film.get('release_date', '')[:4]
        rating = film.get('rating', '') or film.get('ratingKinopoisk', '')
        film_id = extract_film_id(film)
        description = film.get('description', '') or film.get('overview', '')
        poster_url = film.get('posterUrlPreview') or film.get('poster_url') or film.get('posterUrl')

        # Формируем полное описание
        text = f"🎬 *{title}*"
        if year:
            text += f" ({year})"

        if rating:
            text += f"\n⭐ Рейтинг: {rating}"

        # Жанры
        genres = film.get('genres', [])
        if isinstance(genres, list):
            if genres and isinstance(genres[0], dict):
                genre_names = [g.get('genre', '') for g in genres[:3]]
            else:
                genre_names = genres[:3]
            if genre_names:
                text += f"\n🎭 Жанр: {', '.join(genre_names)}"

        # Полное описание
        if description:
            text += f"\n\n📝 *Описание:*\n{description}"

        # Кнопки действий
        keyboard = []

        if from_watchlist:
            # Для watchlist добавляем кнопку удаления
            keyboard.append([
                InlineKeyboardButton("🗑️ Удалить из Watchlist", callback_data=f"remove_{film_id}")
            ])
        else:
            # Только кнопка добавления в Watchlist
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

# ==================== ОСНОВНЫЕ ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    welcome_text = f"""
🎬 Привет, {user.first_name}! Я КиноПроводник — твой киногид!

✨ *Что я умею:*
• 🔍 Искать фильмы и сериалы
• 🎯 Подбирать фильмы по жанрам
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
• Топ-250 лучших фильмов (случайные из топа)
• Подбор по жанрам (10 случайных фильмов с рейтингом ≥7.0)
• Случайные рекомендации
• Список «Посмотреть позже»

⌨️ *Используй кнопки или команды:*
• /start — запустить бота
• /search <название> — поиск фильма
• /top — случайные фильмы из топ-250  
• /random — случайный фильм с рейтингом ≥8.5
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

async def show_test_results(update, query):
    """Показать тестовые результаты (когда API не работает)"""
    logger.info(f"🔍 Тестовый поиск: '{query}'")

    for film in POPULAR_MOVIES[:2]:
        await send_film_card(update, film)

async def show_top250(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /top - показывает случайные фильмы из топ-250"""
    await update.message.reply_text("⭐ Загружаю случайные фильмы из топ-250...")

    if not api_client or not api_client.is_active:
        # Тестовые данные
        for film in POPULAR_MOVIES:
            await send_film_card(update, film)
        return

    try:
        # Получаем 3 случайные страницы из топа и выбираем 10 случайных фильмов
        all_films = []

        for _ in range(3):
            page = random.randint(1, 13)  # В топе 250 фильмов, по 20 на странице
            result = api_client.get_top_films(page=page)
            films = result.get('films', [])

            # Фильтруем фильмы с рейтингом
            for film in films:
                rating_str = film.get('rating', '0')
                try:
                    rating = float(rating_str) if rating_str else 0
                    if rating >= 6.0:  # Минимальный рейтинг для показа
                        all_films.append(film)
                except (ValueError, TypeError):
                    continue

        # Перемешиваем и выбираем 10 случайных
        if all_films:
            random.shuffle(all_films)
            selected_films = all_films[:10]

            # Получаем полную информацию для каждого фильма
            for film in selected_films:
                film_id = extract_film_id(film)
                if film_id:
                    details = api_client.get_film_details(film_id)
                    if details:
                        # Объединяем основную информацию с деталями
                        film.update(details)

                await send_film_card(update, film)

                # Небольшая пауза между отправками, чтобы не перегружать API
                import asyncio
                await asyncio.sleep(0.5)
        else:
            await update.message.reply_text(
                "❌ Не удалось загрузить фильмы из топа. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка загрузки топа: {e}")
        # Показываем локальные фильмы как запасной вариант
        for film in POPULAR_MOVIES:
            await send_film_card(update, film)

async def random_real_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /random - случайный фильм из КиноПоиска с рейтингом ≥8.5"""
    await update.message.reply_text("🎲 Ищу случайный фильм с рейтингом от 8.5...")

    try:
        movie = await get_random_movie_from_api()

        if movie:
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

async def get_random_movie_from_api() -> dict:
    """Получить случайный фильм из КиноПоиска с рейтингом не ниже 8.5"""
    if not api_client or not api_client.is_active:
        return random.choice(POPULAR_MOVIES)

    try:
        # Используем метод из kinopoisk_client
        movie = api_client.get_random_high_rated_movie(min_rating=8.5)
        if movie:
            return movie

        # Если не нашли, используем локальный список
        return random.choice(POPULAR_MOVIES)

    except Exception as e:
        logger.error(f"Ошибка получения случайного фильма: {e}")
        return random.choice(POPULAR_MOVIES)

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
                'filmId': item['movie_id'],
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
    """Поиск фильмов по жанру - 10 случайных фильмов"""
    await update.message.reply_text(f"🎭 Ищу фильмы в жанре *{genre}*...", parse_mode='Markdown')

    if not api_client or not api_client.is_active:
        # Тестовые данные для жанра
        await update.message.reply_text(
            f"🎭 *Фильмы в жанре {genre}:*\n\n"
            "⚠️ API не активен, показаны примеры",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        for film in POPULAR_MOVIES[:3]:
            await send_film_card(update, film)
        return

    try:
        genre_id = GENRE_MAP.get(genre.lower())
        if not genre_id:
            await update.message.reply_text(f"Жанр «{genre}» не найден в базе.")
            return

        # Собираем фильмы с нескольких страниц без ограничения по рейтингу
        all_films = []

        for page in range(1, 6):  # Проверяем первые 5 страниц
            try:
                # Убрал rating_from=70 - теперь ищем все фильмы жанра
                result = api_client.get_films_by_filters(
                    genre_id=genre_id,
                    page=page
                )

                films = result.get('items', [])
                if not films:
                    break

                # Добавляем все фильмы без фильтрации по рейтингу
                all_films.extend(films)

                # Если уже достаточно фильмов, выходим
                if len(all_films) >= 50:  # Собираем до 50 фильмов для выбора
                    break

            except Exception as page_error:
                logger.error(f"Ошибка на странице {page} для жанра {genre}: {page_error}")
                continue

        if not all_films:
            # Если не нашли фильмы, пробуем альтернативный способ - поиск по названию жанра
            logger.info(f"Пробую альтернативный поиск для жанра {genre}")

            # Пробуем найти фильмы через поиск по ключевым словам
            genre_keywords = {
                "мелодрама": ["любовь", "романтика", "любовная история"],
                "драма": ["драма", "трагедия", "эмоции"],
                "комедия": ["комедия", "юмор", "смех"],
                "боевик": ["боевик", "экшн", "сражения"],
                "ужасы": ["ужасы", "хоррор", "страх"],
                "фантастика": ["фантастика", "футуризм", "космос"],
                "детектив": ["детектив", "расследование", "тайна"],
                "триллер": ["триллер", "саспенс", "напряжение"],
                "приключения": ["приключения", "путешествия", "экспедиция"]
            }

            keywords = genre_keywords.get(genre.lower(), [genre])

            for keyword in keywords:
                try:
                    search_result = api_client.search_films(keyword)
                    search_films = search_result.get('films', [])

                    if search_films:
                        # Фильтруем фильмы, которые могут быть нужного жанра
                        for film in search_films:
                            film_genres = film.get('genres', [])
                            if isinstance(film_genres, list):
                                # Проверяем названия жанров
                                genre_names = []
                                for g in film_genres:
                                    if isinstance(g, dict):
                                        genre_names.append(g.get('genre', '').lower())
                                    elif isinstance(g, str):
                                        genre_names.append(g.lower())

                                # Если жанр совпадает, добавляем
                                if genre.lower() in genre_names:
                                    all_films.append(film)

                except Exception as search_error:
                    logger.error(f"Ошибка поиска по ключевому слову {keyword}: {search_error}")
                    continue

        if not all_films:
            await update.message.reply_text(
                f"😔 Не найдено фильмов в жанре «{genre}».\n"
                "Попробуйте другой жанр.",
                reply_markup=get_genre_keyboard()
            )
            return

        # Выбираем до 10 случайных фильмов
        if len(all_films) > 10:
            selected_films = random.sample(all_films, 10)
        else:
            selected_films = all_films

        # Показываем найденные фильмы
        await update.message.reply_text(
            f"🎭 *Найдено {len(all_films)} фильмов в жанре {genre}*\n"
            f"Показываю {len(selected_films)} случайных фильмов:",
            parse_mode='Markdown'
        )

        # Получаем полную информацию и показываем каждый фильм
        films_shown = 0
        for film in selected_films:
            try:
                film_id = extract_film_id(film)
                if film_id:
                    try:
                        # Получаем полную информацию о фильме
                        details = api_client.get_film_details(film_id)
                        if details:
                            # Объединяем основную информацию с деталями
                            film.update(details)
                    except Exception as e:
                        logger.error(f"Ошибка получения деталей фильма {film_id}: {e}")

                await send_film_card(update, film)
                films_shown += 1

                # Небольшая пауза между отправками, чтобы не перегружать API
                import asyncio
                await asyncio.sleep(0.5)

            except Exception as film_error:
                logger.error(f"Ошибка показа фильма: {film_error}")
                continue

        if films_shown == 0:
            await update.message.reply_text(
                f"😔 Не удалось показать фильмы в жанре «{genre}».\n"
                "Попробуйте другой жанр.",
                reply_markup=get_genre_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка поиска по жанру: {e}", exc_info=True)
        await update.message.reply_text(
            f"🎭 *Фильмы в жанре {genre}:*\n\n"
            "⚠️ Ошибка API, показаны примеры",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        # Показываем тестовые данные
        for film in POPULAR_MOVIES[:3]:
            try:
                await send_film_card(update, film)
            except:
                pass
# ==================== ОБРАБОТЧИК INLINE-КНОПОК ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline-кнопок"""
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Нажата inline-кнопка: {data}")

    if data.startswith('watch_'):
        # Добавить в Watchlist
        try:
            film_id = data.split('_')[1]

            # Получаем информацию о фильме
            film_info = {}
            if api_client:
                try:
                    film_info = api_client.get_film_details(int(film_id))
                except:
                    # Если не удалось получить детали, создаем базовую информацию
                    film_info = {'nameRu': f'Фильм ID {film_id}'}

            # Создаем данные фильма
            movie_data = {
                'id': int(film_id),
                'title': film_info.get('nameRu') or f'Фильм ID {film_id}',
                'year': film_info.get('year', ''),
                'poster_url': film_info.get('posterUrl') or film_info.get('posterUrlPreview', '')
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

    else:
        # Неизвестная кнопка
        await query.edit_message_text(f"Действие: {data}")