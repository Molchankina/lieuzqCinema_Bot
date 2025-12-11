import os
import sys
from bot.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize database"""
    logger.info("Initializing database...")

    try:
        # Initialize database
        SessionLocal = init_db()
        logger.info("Database initialized successfully")

        # Test connection
        session = SessionLocal()
        session.execute("SELECT 1")
        session.close()

        logger.info("Database connection test successful")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()