from datetime import datetime
from sqlalchemy.orm import Session
from bot.database import User, Movie, Watchlist, get_session
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manager for database operations"""

    def __init__(self, session: Session = None):
        self.session = session or get_session()

    # User operations
    def get_or_create_user(self, telegram_id: int, username: str = None,
                           first_name: str = None, last_name: str = None) -> User:
        """Get or create user"""
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
            logger.info(f"New user created: {telegram_id}")

        return user

    # Movie operations
    def get_movie_by_tmdb_id(self, tmdb_id: int, media_type: str) -> Optional[Movie]:
        """Get movie by TMDB ID"""
        return self.session.query(Movie).filter_by(
            tmdb_id=tmdb_id,
            media_type=media_type
        ).first()

    def create_movie(self, tmdb_data: dict) -> Movie:
        """Create movie record from TMDB data"""
        # Check if movie already exists
        existing = self.get_movie_by_tmdb_id(
            tmdb_data['id'],
            tmdb_data.get('media_type', 'movie')
        )

        if existing:
            return existing

        # Create new movie record
        movie = Movie(
            tmdb_id=tmdb_data['id'],
            title=tmdb_data.get('title') or tmdb_data.get('name', ''),
            original_title=tmdb_data.get('original_title') or tmdb_data.get('original_name', ''),
            release_date=tmdb_data.get('release_date') or tmdb_data.get('first_air_date', ''),
            overview=tmdb_data.get('overview', ''),
            poster_path=tmdb_data.get('poster_path', ''),
            backdrop_path=tmdb_data.get('backdrop_path', ''),
            media_type=tmdb_data.get('media_type', 'movie'),
            genres=', '.join([g['name'] for g in tmdb_data.get('genres', [])]) if 'genres' in tmdb_data else '',
            vote_average=tmdb_data.get('vote_average'),
            vote_count=tmdb_data.get('vote_count'),
            popularity=tmdb_data.get('popularity'),
            runtime=tmdb_data.get('runtime'),
            status=tmdb_data.get('status')
        )

        self.session.add(movie)
        self.session.commit()
        return movie

    # Watchlist operations
    def add_to_watchlist(self, user_id: int, movie_id: int) -> Optional[Watchlist]:
        """Add movie to user's watchlist"""
        # Check if already in watchlist
        existing = self.session.query(Watchlist).filter_by(
            user_id=user_id,
            movie_id=movie_id
        ).first()

        if existing:
            return None

        watchlist_item = Watchlist(
            user_id=user_id,
            movie_id=movie_id,
            reminder_enabled=True
        )

        self.session.add(watchlist_item)
        self.session.commit()
        return watchlist_item

    def get_watchlist(self, user_id: int, limit: int = 50) -> List[Watchlist]:
        """Get user's watchlist"""
        return self.session.query(Watchlist).join(Movie).filter(
            Watchlist.user_id == user_id,
            Watchlist.watched == False
        ).order_by(Watchlist.added_at.desc()).limit(limit).all()

    def mark_as_watched(self, watchlist_id: int, user_id: int) -> bool:
        """Mark movie as watched"""
        watchlist_item = self.session.query(Watchlist).filter_by(
            id=watchlist_id,
            user_id=user_id
        ).first()

        if watchlist_item:
            watchlist_item.watched = True
            watchlist_item.watched_at = datetime.utcnow()
            self.session.commit()
            return True

        return False

    def remove_from_watchlist(self, watchlist_id: int, user_id: int) -> bool:
        """Remove movie from watchlist"""
        watchlist_item = self.session.query(Watchlist).filter_by(
            id=watchlist_id,
            user_id=user_id
        ).first()

        if watchlist_item:
            self.session.delete(watchlist_item)
            self.session.commit()
            return True

        return False

    def close(self):
        """Close database session"""
        self.session.close()

# Factory function
def get_db_manager() -> DatabaseManager:
    return DatabaseManager()

# Context manager decorator
def with_db_session(func):
    """Decorator for automatic database session management"""
    def wrapper(*args, **kwargs):
        db_manager = DatabaseManager()
        try:
            result = func(db_manager=db_manager, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            db_manager.close()
    return wrapper