# bot/db_utils.py - УПРОЩЕННЫЙ для работы Watchlist

import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Упрощенный менеджер БД для Watchlist"""

    def __init__(self):
        self.watchlist = []  # Временное хранилище вместо БД
        logger.info("✅ Инициализирован упрощенный менеджер БД")

    def add_to_watchlist(self, user_id: int, movie_data: dict) -> bool:
        """Добавить фильм в Watchlist (упрощенная версия)"""
        try:
            # Проверяем, нет ли уже такого фильма у пользователя
            for item in self.watchlist:
                if item.get('user_id') == user_id and item.get('movie_id') == movie_data.get('id'):
                    return False

            # Добавляем новый фильм
            watchlist_item = {
                'id': len(self.watchlist) + 1,
                'user_id': user_id,
                'movie_id': movie_data.get('id'),
                'title': movie_data.get('title', 'Без названия'),
                'year': movie_data.get('year', ''),
                'added_at': datetime.now()
            }

            self.watchlist.append(watchlist_item)
            logger.info(f"Добавлен фильм в Watchlist: {movie_data.get('title')}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления в Watchlist: {e}")
            return False

    def get_watchlist(self, user_id: int) -> List[Dict]:
        """Получить Watchlist пользователя"""
        try:
            user_watchlist = [item for item in self.watchlist if item.get('user_id') == user_id]
            return user_watchlist[:20]  # Ограничиваем 20 фильмами
        except Exception as e:
            logger.error(f"Ошибка получения Watchlist: {e}")
            return []

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        """Удалить фильм из Watchlist"""
        try:
            initial_length = len(self.watchlist)
            self.watchlist = [item for item in self.watchlist
                              if not (item.get('user_id') == user_id and item.get('movie_id') == movie_id)]

            return len(self.watchlist) < initial_length
        except Exception as e:
            logger.error(f"Ошибка удаления из Watchlist: {e}")
            return False

# Фабрика для создания менеджера БД
def get_db_manager() -> DatabaseManager:
    return DatabaseManager()