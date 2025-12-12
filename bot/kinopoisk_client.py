# bot/kinopoisk_client.py - полная рабочая версия

import os
import logging
import requests
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

class KinopoiskClient:
    def __init__(self):
        self.api_key = os.getenv('KINOPOISK_API_KEY')

        # Проверяем наличие ключа
        if not self.api_key or self.api_key.startswith('your_'):
            logger.error("❌ KINOPOISK_API_KEY не установлен!")
            logger.error("Получите ключ на https://kinopoiskapiunofficial.tech")
            self.api_key = None

        self.base_url = "https://kinopoiskapiunofficial.tech/api"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "MovieMateBot/1.0"
        }

        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key

        self.is_active = bool(self.api_key)
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        if self.is_active:
            logger.info("✅ КиноПоиск клиент инициализирован")
        else:
            logger.warning("⚠️ КиноПоиск клиент НЕ активен")

    def search_films(self, query: str, page: int = 1) -> Dict:
        """Поиск фильмов и сериалов"""
        if not self.is_active:
            logger.error("КиноПоиск API не активен")
            return {"films": [], "searchFilmsCountResult": 0}

        url = f"{self.base_url}/v2.1/films/search-by-keyword"
        params = {
            "keyword": query,
            "page": page
        }

        try:
            logger.info(f"Ищу: '{query}'")
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                count = data.get("searchFilmsCountResult", 0)
                films = data.get("films", [])
                logger.info(f"Найдено результатов: {count}")
                return data
            elif response.status_code == 401:
                logger.error("❌ Неверный API ключ КиноПоиска")
                return {"films": [], "searchFilmsCountResult": 0, "error": "Invalid API key"}
            else:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                return {"films": [], "searchFilmsCountResult": 0}

        except requests.exceptions.Timeout:
            logger.error("⏱️ Таймаут запроса к КиноПоиску")
            return {"films": [], "searchFilmsCountResult": 0}
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к КиноПоиску: {e}")
            return {"films": [], "searchFilmsCountResult": 0}

    def get_film_details(self, film_id: int) -> Dict:
        """Получение деталей фильма"""
        if not self.is_active:
            return {}

        url = f"{self.base_url}/v2.2/films/{film_id}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Ошибка получения деталей фильма {film_id}: {e}")
            return {}

    def get_similar_films(self, film_id: int) -> List[Dict]:
        """Похожие фильмы"""
        if not self.is_active:
            return []

        url = f"{self.base_url}/v2.2/films/{film_id}/similars"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            return []
        except Exception as e:
            logger.error(f"Ошибка получения похожих фильмов {film_id}: {e}")
            return []

    def get_top_films(self, page: int = 1, top_type: str = "TOP_250_BEST_FILMS") -> Dict:
        """Топ фильмов"""
        if not self.is_active:
            return {"films": []}

        url = f"{self.base_url}/v2.2/films/top"
        params = {
            "type": top_type,
            "page": page
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"films": []}
        except Exception as e:
            logger.error(f"Ошибка получения топа: {e}")
            return {"films": []}

    def get_films_by_filters(self, genre_id: Optional[int] = None,
                             year_from: Optional[int] = None,
                             year_to: Optional[int] = None,
                             rating_from: Optional[int] = None,
                             page: int = 1) -> Dict:
        """Фильмы по фильтрам"""
        if not self.is_active:
            return {"items": []}

        url = f"{self.base_url}/v2.2/films"
        params = {
            "order": "RATING",
            "type": "ALL",
            "ratingFrom": rating_from or 0,
            "ratingTo": 10,
            "yearFrom": year_from or 1900,
            "yearTo": year_to or 2025,
            "page": page
        }

        if genre_id:
            params["genres"] = genre_id

        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"items": []}
        except Exception as e:
            logger.error(f"Ошибка фильтрации: {e}")
            return {"items": []}

# Глобальный экземпляр
kinopoisk_client = KinopoiskClient()