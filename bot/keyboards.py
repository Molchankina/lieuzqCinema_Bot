from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Главное меню с emoji"""
    keyboard = [
        ["🎬 Поиск фильма", "📺 Поиск сериала"],
        ["⭐ Избранное", "📋 Watchlist"],
        ["🎲 Случайный", "🔥 Топ"],
        ["⚙️ Настройки", "ℹ️ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_genre_keyboard():
    """Клавиатура жанров"""
    keyboard = [
        ["🎭 Драма", "😂 Комедия", "❤️ Мелодрама"],
        ["🚀 Фантастика", "👻 Ужасы", "🔍 Детектив"],
        ["🎬 Боевик", "🧩 Триллер", "🤠 Вестерн"],
        ["🔙 Назад"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_movie_actions(movie_id):
    """Действия для фильма"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💾 В Watchlist", callback_data=f"add_{movie_id}"),
            InlineKeyboardButton("🎯 Похожие", callback_data=f"similar_{movie_id}")
        ],
        [
            InlineKeyboardButton("📝 Подробнее", callback_data=f"info_{movie_id}"),
            InlineKeyboardButton("🎬 Трейлер", callback_data=f"trailer_{movie_id}")
        ]
    ])