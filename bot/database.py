from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    language_code = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    tmdb_id = Column(Integer, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    original_title = Column(String(500))
    release_date = Column(String(20))
    overview = Column(Text)
    poster_path = Column(String(500))
    backdrop_path = Column(String(500))
    media_type = Column(String(20))  # 'movie' или 'tv'
    genres = Column(Text)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    runtime = Column(Integer)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    watchlist_entries = relationship("Watchlist", back_populates="movie")

class Watchlist(Base):
    __tablename__ = 'watchlist'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    watched = Column(Boolean, default=False)
    watched_at = Column(DateTime, nullable=True)
    reminder_enabled = Column(Boolean, default=False)
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="watchlist_items")
    movie = relationship("Movie", back_populates="watchlist_entries")

    # Unique constraint
    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='_user_movie_uc'),)

# Database session management
SessionLocal = None

def init_db():
    """Initialize database connection"""
    global SessionLocal

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        # Local development with SQLite
        database_url = 'sqlite:///movies.db'
        logger.info("Using SQLite for local development")
    elif database_url.startswith('postgres://'):
        # Railway uses postgres://, need to replace with postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    # Parameters for PostgreSQL
    engine_kwargs = {}
    if database_url.startswith('postgresql://'):
        engine_kwargs.update({
            'pool_size': 5,
            'max_overflow': 10,
            'pool_pre_ping': True,
            'pool_recycle': 300,
        })

    try:
        engine = create_engine(database_url, **engine_kwargs)

        # Test connection
        with engine.connect() as conn:
            logger.info(f"Successfully connected to database: {database_url}")

        # Create tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created/verified")

        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        return SessionLocal

    except Exception as e:
        logger.error(f"Database connection error: {e}")

        # Fallback to SQLite if PostgreSQL is not available
        if database_url.startswith('postgresql://'):
            logger.info("Trying SQLite as fallback")
            database_url = 'sqlite:///movies.db'
            engine = create_engine(database_url)
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
            return SessionLocal
        raise

def get_session():
    """Get database session"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = init_db()
    return SessionLocal()