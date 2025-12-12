# bot/__init__.py
"""
MovieMate Bot - Бот для поиска фильмов и сериалов
"""

__version__ = '1.0.0'
__author__ = 'MovieMate Team'

# Экспортируем основные функции и классы
from .main import main
from .handlers import start, handle_message, button_handler
from .database import init_db, User, Movie, Watchlist
from .tmdb_client import tmdb_client

__all__ = [
    'main',
    'start',
    'handle_message',
    'button_handler',
    'init_db',
    'User',
    'Movie',
    'Watchlist',
    'tmdb_client'
]