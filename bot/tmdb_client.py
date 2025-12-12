# bot/tmdb_client.py - улучшенная версия

import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv('TMDB_API_KEY')
        if not self.api_key or self.api_key.startswith('your_'):
            logger.warning("⚠️ TMDB_API_KEY не установлен. Поиск будет недоступен.")
            self.api_key = None

        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "accept": "application/json"
        }

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        self.is_active = bool(self.api_key)
        logger.info(f"TMDB клиент: {'АКТИВЕН' if self.is_active else 'НЕАКТИВЕН'}")

    def search_movies(self, query: str) -> List[Dict]:
        """Поиск фильмов"""
        if not self.is_active:
            logger.error("❌ TMDB_API_KEY не установлен. Не могу выполнить поиск.")
            return []

        url = f"{self.base_url}/search/multi"
        params = {
            "query": query,
            "language": "ru-RU",
            "page": 1
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:5]
        except Exception as e:
            logger.error(f"Ошибка поиска TMDB: {e}")
            return []

# Создаем глобальный экземпляр
tmdb_client = TMDBClient()