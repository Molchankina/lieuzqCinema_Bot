# bot/db_utils.py

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from bot.database import User, Movie, Watchlist, get_session
from typing import Optional, List

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    def get_or_create_user(self, telegram_id: int, username: str = None,
                           first_name: str = None, last_name: str = None) -> User:
        """Получить или создать пользователя"""
        try:
            user = self.session.query(User).filter_by(telegram_id=telegram_id).first()

            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                self.session.add(user)
                self.session.commit()
                logger.info(f"Создан новый пользователь: {telegram_id}")

            return user
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}")
            self.session.rollback()
            return None

    def add_to_watchlist(self, user_id: int, movie_data: dict) -> bool:
        """Добавить фильм в watchlist"""
        try:
            # Сначала ищем пользователя
            user = self.session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                # Создаем пользователя если его нет
                user = User(telegram_id=user_id)
                self.session.add(user)
                self.session.commit()

            # Проверяем, есть ли уже такой фильм
            existing_movie = self.session.query(Movie).filter_by(
                tmdb_id=movie_data.get('id')
            ).first()

            if not existing_movie:
                # Создаем запись о фильме
                existing_movie = Movie(
                    tmdb_id=movie_data.get('id', 0),
                    title=movie_data.get('title', ''),
                    original_title=movie_data.get('original_title', ''),
                    release_date=movie_data.get('release_date', ''),
                    overview=movie_data.get('overview', ''),
                    poster_url=movie_data.get('poster_path', ''),
                    media_type=movie_data.get('media_type', 'movie'),
                    genres=movie_data.get('genres', ''),
                    vote_average=movie_data.get('vote_average', 0.0)
                )
                self.session.add(existing_movie)
                self.session.commit()

            # Проверяем, не добавлен ли уже в watchlist
            existing_watchlist = self.session.query(Watchlist).filter_by(
                user_id=user.id,
                movie_id=existing_movie.id
            ).first()

            if existing_watchlist:
                return False  # Уже в watchlist

            # Добавляем в watchlist
            watchlist_item = Watchlist(
                user_id=user.id,
                movie_id=existing_movie.id
            )
            self.session.add(watchlist_item)
            self.session.commit()

            return True

        except Exception as e:
            logger.error(f"Ошибка добавления в watchlist: {e}")
            self.session.rollback()
            return False

    def get_watchlist(self, user_id: int, limit: int = 20) -> List[dict]:
        """Получить watchlist пользователя"""
        try:
            results = self.session.query(Watchlist, Movie) \
                .join(Movie, Watchlist.movie_id == Movie.id) \
                .filter(Watchlist.user_id == user_id) \
                .filter(Watchlist.watched == False) \
                .order_by(Watchlist.added_at.desc()) \
                .limit(limit) \
                .all()

            watchlist = []
            for watchlist_item, movie in results:
                watchlist.append({
                    'id': watchlist_item.id,
                    'movie_id': movie.id,
                    'title': movie.title,
                    'year': movie.release_date[:4] if movie.release_date else '',
                    'added_at': watchlist_item.added_at
                })

            return watchlist
        except Exception as e:
            logger.error(f"Ошибка при получении watchlist: {e}")
            return []

    def mark_as_watched(self, watchlist_id: int, user_id: int) -> bool:
        """Отметить фильм как просмотренный"""
        try:
            item = self.session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()

            if item:
                item.watched = True
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при отметке как просмотренного: {e}")
            self.session.rollback()
            return False

    def remove_from_watchlist(self, watchlist_id: int, user_id: int) -> bool:
        """Удалить из watchlist"""
        try:
            item = self.session.query(Watchlist).filter_by(
                id=watchlist_id,
                user_id=user_id
            ).first()

            if item:
                self.session.delete(item)
                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении из watchlist: {e}")
            self.session.rollback()
            return False

    def close(self):
        """Закрыть сессию"""
        self.session.close()

# Фабрика для создания менеджера БД
def get_db_manager() -> DatabaseManager:
    """Получить экземпляр менеджера БД (функция, которую ищет handlers.py)"""
    return DatabaseManager()