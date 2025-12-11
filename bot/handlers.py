from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import re
from typing import Optional, List, Dict
from bot.tmdb_client import tmdb_client
from bot.db_utils import get_db_manager, with_db_session
from datetime import datetime

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_text = f"""
🎬 Привет, {user.first_name}! Я MovieMate — твой персональный киногид!

✨ Что я умею:
• 🔍 Искать фильмы и сериалы по названию, жанру, году
• 🎯 Подбирать похожие фильмы ("Что посмотреть, если нравится Интерстеллар?")
• 💾 Сохранять понравившиеся фильмы в "Посмотреть позже"
• 🔔 Напоминать о выходе новых серий твоих любимых сериалов

💡 Просто напиши:
• "Хочу детектив 90-х"
• "Поиск: Матрица"
• "Что посмотреть, если нравится Интерстеллар?"
• Или используй команды ниже👇
    """

    keyboard = [
        [InlineKeyboardButton("🔍 Поиск фильма", callback_data="search_movie")],
        [InlineKeyboardButton("📺 Мои сериалы", callback_data="my_series")],
        [InlineKeyboardButton("🎯 Рекомендации", callback_data="recommendations")],
        [InlineKeyboardButton("📋 Мой watchlist", callback_data="watchlist")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    # Save user to database
    db_manager = get_db_manager()
    try:
        db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
    finally:
        db_manager.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 *Доступные команды:*

/start - Запустить бота
/help - Эта справка
/search <запрос> - Поиск фильмов и сериалов
/similar <название> - Похожие фильмы
/watchlist - Мой список для просмотра

💡 *Примеры запросов:*
• "Хочу детектив 90-х"
• "Поиск: Матрица"
• "Что посмотреть, если нравится Интерстеллар?"
• "Найди комедии 2000-х"

*Просто напиши в чат:* "хочу посмотреть комедию" или "ищи триллер"
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command"""
    if not context.args:
        await update.message.reply_text("Укажи что искать:\n/search Матрица\n/search детектив")
        return

    query = ' '.join(context.args)
    await search_movies(update, context, query)

async def similar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /similar command"""
    if not context.args:
        await update.message.reply_text("Укажи фильм для поиска похожих:\n/similar Матрица")
        return

    query = ' '.join(context.args)
    await find_similar(update, context, query)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower()

    # Extract search query
    if any(word in text for word in ['хочу', 'ищи', 'найди', 'поиск:', 'search:']):
        query = text.split(':', 1)[-1].strip() if ':' in text else text
        await search_movies(update, context, query)

    # Similar movies request
    elif any(phrase in text for phrase in ['похож', 'если нравится', 'similar to']):
        if 'если нравится' in text:
            query = text.split('если нравится', 1)[-1].strip()
        else:
            # Extract movie name from various patterns
            patterns = [
                r'похож(ие|ее) на (.+)',
                r'что посмотреть если нравится (.+)',
                r'similar to (.+)'
            ]
            query = text
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    query = match.group(1).strip()
                    break

        await find_similar(update, context, query)

    # Genre and year search
    elif any(genre in text for genre in ['детектив', 'комедия', 'драма', 'фантастика',
                                         'боевик', 'триллер', 'ужасы', 'мелодрама']):
        # Extract year if present
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        year = year_match.group(0) if year_match else None

        # Extract genre
        genre = None
        for g in ['детектив', 'комедия', 'драма', 'фантастика',
                  'боевик', 'триллер', 'ужасы', 'мелодрама']:
            if g in text:
                genre = g
                break

        if genre:
            await search_by_genre_year(update, context, genre, year)
        else:
            await search_movies(update, context, text)

    else:
        # Default to search
        await search_movies(update, context, text)

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Search movies and TV shows"""
    await update.message.reply_text(f"🔍 Ищу: {query}...")

    # Extract year from query
    year = None
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', query)
    if year_match:
        year = year_match.group(0)
        # Remove year from query for better search
        query = re.sub(r'\b(19\d{2}|20\d{2})\b', '', query).strip()

    results = tmdb_client.search_movies(query, year=year)

    if not results:
        await update.message.reply_text("😔 Ничего не найдено. Попробуй другой запрос.")
        return

    for item in results[:5]:  # Show first 5 results
        title = item.get('title') or item.get('name', 'Без названия')
        media_type = "🎬 Фильм" if item.get('media_type') == 'movie' else "📺 Сериал"
        year = item.get('release_date', '')[:4] or item.get('first_air_date', '')[:4]
        rating = item.get('vote_average', '?')

        text = f"{media_type}: *{title}* ({year})\n"
        if rating and rating != '?':
            text += f"⭐ Рейтинг: {rating}/10\n"

        if item.get('overview'):
            text += f"\n{item['overview'][:200]}..."

        keyboard = [[
            InlineKeyboardButton("💾 В watchlist", callback_data=f"add_{item['id']}_{item['media_type']}"),
            InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{item['id']}_{item['media_type']}")
        ]]

        # Send poster if available
        if item.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{item['poster_path']}"
            try:
                await update.message.reply_photo(
                    photo=poster_url,
                    caption=text,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                continue
            except Exception as e:
                logger.error(f"Error sending photo: {e}")

        # Fallback to text only
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def search_by_genre_year(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               genre: str, year: Optional[str] = None):
    """Search by genre and year"""
    await update.message.reply_text(f"🔍 Ищу {genre}" + (f" за {year} год" if year else "") + "...")

    results = tmdb_client.discover_movies(genre=genre, year=year)

    if not results:
        await update.message.reply_text(f"😔 Не нашёл {genre}" + (f" за {year} год" if year else ""))
        return

    text = f"🎬 *{genre.capitalize()}" + (f" {year} года" if year else "") + "*\n\n"

    for i, item in enumerate(results[:5], 1):
        title = item.get('title', 'Без названия')
        year = item.get('release_date', '')[:4] if item.get('release_date') else '?'
        rating = item.get('vote_average', '?')

        text += f"{i}. *{title}* ({year})"
        if rating and rating != '?':
            text += f" ⭐ {rating}/10"
        text += "\n"

    await update.message.reply_text(text, parse_mode='Markdown')

async def find_similar(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Find similar movies"""
    # First search for the movie
    results = tmdb_client.search_movies(query.strip())

    if not results:
        await update.message.reply_text("😔 Не нашёл такой фильм. Уточни название.")
        return

    film = results[0]
    film_id = film['id']
    media_type = film.get('media_type', 'movie')
    film_title = film.get('title') or film.get('name', 'Фильм')

    await update.message.reply_text(f"🔍 Ищу похожее на *{film_title}*...", parse_mode='Markdown')

    similar = tmdb_client.get_similar_movies(film_id, media_type)

    if not similar:
        await update.message.reply_text("😔 Не нашёл похожих фильмов.")
        return

    text = f"🎯 *Похоже на {film_title}:*\n\n"

    for i, item in enumerate(similar[:5], 1):
        title = item.get('title') or item.get('name', 'Без названия')
        year = item.get('release_date', '')[:4] or item.get('first_air_date', '')[:4] or '?'
        rating = item.get('vote_average', '?')

        text += f"{i}. *{title}* ({year})"
        if rating and rating != '?':
            text += f" ⭐ {rating}/10"
        text += "\n"

    await update.message.reply_text(text, parse_mode='Markdown')

async def show_watchlist(update: Update, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
    """Show user's watchlist"""
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        message_id = query.message.message_id
    else:
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        message_id = None

    db_manager = get_db_manager()
    try:
        watchlist_items = db_manager.get_watchlist(user_id)

        if not watchlist_items:
            text = "📭 Твой watchlist пуст!\n\nДобавляй фильмы кнопкой '💾 В watchlist'"
            if hasattr(update, 'callback_query'):
                await update.callback_query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return

        text = "📋 *Твой Watchlist:*\n\n"
        keyboard = []

        for i, watchlist in enumerate(watchlist_items[:10], 1):
            movie = watchlist.movie
            text += f"{i}. *{movie.title}* ({movie.release_date[:4] if movie.release_date else '?'})\n"
            keyboard.append([
                InlineKeyboardButton(f"✅ Посмотрел {i}", callback_data=f"watched_{watchlist.id}"),
                InlineKeyboardButton(f"🗑 Удалить {i}", callback_data=f"remove_{watchlist.id}")
            ])

        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    finally:
        db_manager.close()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith('add_'):
        # Add to watchlist
        _, item_id, media_type = data.split('_')
        await add_to_watchlist(query, int(item_id), media_type)

    elif data.startswith('info_'):
        # Show details
        _, item_id, media_type = data.split('_')
        await show_movie_details(query, int(item_id), media_type)

    elif data.startswith('watched_'):
        # Mark as watched
        _, watchlist_id = data.split('_')
        await mark_as_watched(query, int(watchlist_id))

    elif data.startswith('remove_'):
        # Remove from watchlist
        _, watchlist_id = data.split('_')
        await remove_from_watchlist(query, int(watchlist_id))

    elif data == 'watchlist':
        await show_watchlist(query)

    elif data == 'search_movie':
        await query.edit_message_text("Напиши что искать:\nНапример: 'Матрица' или 'Детектив 90-х'")

async def add_to_watchlist(query, item_id: int, media_type: str):
    """Add movie to watchlist"""
    db_manager = get_db_manager()
    try:
        user_id = query.from_user.id

        # Get movie details from TMDB
        details = tmdb_client.get_movie_details(item_id, media_type)
        if not details:
            await query.edit_message_text("❌ Не удалось получить информацию о фильме")
            return

        # Get or create user
        user = db_manager.get_or_create_user(
            telegram_id=user_id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name
        )

        # Create movie record
        movie = db_manager.create_movie(details)

        # Add to watchlist
        watchlist_item = db_manager.add_to_watchlist(user.id, movie.id)

        if watchlist_item:
            await query.edit_message_text(f"✅ Добавлено в watchlist!\n\n🎬 {movie.title}")
        else:
            await query.edit_message_text(f"🎬 {movie.title}\n\n⚠️ Уже в твоём watchlist!")

    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        await query.edit_message_text("❌ Ошибка при добавлении в watchlist")
    finally:
        db_manager.close()

async def show_movie_details(query, item_id: int, media_type: str):
    """Show detailed movie information"""
    details = tmdb_client.get_movie_details(item_id, media_type)

    if not details:
        await query.edit_message_text("❌ Не удалось загрузить информацию о фильме")
        return

    title = details.get('title') or details.get('name', 'Без названия')
    year = details.get('release_date', '')[:4] or details.get('first_air_date', '')[:4]
    rating = details.get('vote_average', '?')
    runtime = details.get('runtime')
    genres = ', '.join([g['name'] for g in details.get('genres', [])])
    overview = details.get('overview', 'Нет описания')

    text = f"🎬 *{title}* ({year})\n\n"

    if rating and rating != '?':
        text += f"⭐ Рейтинг: {rating}/10\n"

    if runtime:
        text += f"⏱ Длительность: {runtime} мин\n"

    if genres:
        text += f"🎭 Жанры: {genres}\n"

    text += f"\n{overview}"

    # Add cast if available
    credits = details.get('credits', {})
    cast = credits.get('cast', [])
    if cast:
        top_cast = [actor['name'] for actor in cast[:3]]
        text += f"\n\n🎭 В ролях: {', '.join(top_cast)}"

    await query.edit_message_text(text, parse_mode='Markdown')

async def mark_as_watched(query, watchlist_id: int):
    """Mark movie as watched"""
    db_manager = get_db_manager()
    try:
        user_id = query.from_user.id
        success = db_manager.mark_as_watched(watchlist_id, user_id)

        if success:
            await query.edit_message_text("✅ Отмечено как просмотренное!")
        else:
            await query.edit_message_text("❌ Не удалось отметить как просмотренное")
    finally:
        db_manager.close()

async def remove_from_watchlist(query, watchlist_id: int):
    """Remove movie from watchlist"""
    db_manager = get_db_manager()
    try:
        user_id = query.from_user.id
        success = db_manager.remove_from_watchlist(watchlist_id, user_id)

        if success:
            await query.edit_message_text("🗑 Удалено из watchlist!")
        else:
            await query.edit_message_text("❌ Не удалось удалить из watchlist")
    finally:
        db_manager.close()

async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    db_manager = get_db_manager()
    try:
        user_id = update.effective_user.id

        # Get user's watchlist stats
        watchlist_items = db_manager.get_watchlist(user_id)
        watched_count = len([w for w in watchlist_items if w.watched])
        total_count = len(watchlist_items)

        text = f"📊 *Твоя статистика:*\n\n"
        text += f"📋 Всего в watchlist: {total_count}\n"
        text += f"✅ Просмотрено: {watched_count}\n"

        if total_count > 0:
            progress = int((watched_count / total_count) * 100)
            text += f"📈 Прогресс: {progress}%\n"

        await update.message.reply_text(text, parse_mode='Markdown')
    finally:
        db_manager.close()