# bot/database.py

import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime

logger = logging.getLogger(__name__)
Base = declarative_base()

# Глобальные переменные для сессии БД
engine = None
SessionLocal = None

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.now)  # Исправлено

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    kp_id = Column(Integer, index=True)  # Переименовано из tmdb_id
    title = Column(String(500))
    original_title = Column(String(500))
    release_date = Column(String(20))
    overview = Column(Text)
    poster_url = Column(String(500))
    media_type = Column(String(20))  # 'movie' или 'tv'
    genres = Column(Text)
    vote_average = Column(Float)
    created_at = Column(DateTime, default=datetime.now)  # Исправлено

class Watchlist(Base):
    __tablename__ = 'watchlist'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    movie_id = Column(Integer)
    added_at = Column(DateTime, default=datetime.now)  # Исправлено
    watched = Column(Boolean, default=False)

def init_db():
    """Инициализация базы данных"""
    global engine, SessionLocal

    database_url = os.getenv('DATABASE_URL', 'sqlite:///movies.db')

    # Исправляем URL для PostgreSQL на Railway
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    try:
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        logger.info(f"✅ База данных инициализирована: {database_url}")
        return SessionLocal
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")

        # Fallback на SQLite
        if not database_url.startswith('sqlite://'):
            logger.info("Пробую SQLite как запасной вариант")
            engine = create_engine('sqlite:///movies.db')
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            return SessionLocal

        raise

def get_session():
    """Получить сессию базы данных"""
    global SessionLocal
    if SessionLocal is None:
        init_db()
    return scoped_session(SessionLocal)  # Исправлено: возвращаем scoped_session