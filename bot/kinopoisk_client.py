import os
import logging
import requests
from typing import List, Dict, Optional, Union
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class KinopoiskClient:
    """Клиент для работы с КиноПоиском (неофициальное API)"""

    def __init__(self):
        self.api_key = os.getenv('KINOPOISK_API_KEY')
        self.base_url = "https://kinopoiskapiunofficial.tech/api"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Прокси, если нужно (опционально)
        proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }

    def search_films(self, query: str, page: int = 1) -> Dict:
        """Поиск фильмов и сериалов"""
        url = f"{self.base_url}/v2.1/films/search-by-keyword"
        params = {
            "keyword": query,
            "page": page
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка поиска фильмов: {e}")
            return {"films": [], "searchFilmsCountResult": 0}

    def get_film_details(self, film_id: int) -> Dict:
        """Получение деталей фильма"""
        url = f"{self.base_url}/v2.2/films/{film_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения деталей фильма {film_id}: {e}")
            return {}

    def get_film_sequels_and_prequels(self, film_id: int) -> List[Dict]:
        """Сиквелы и приквелы"""
        url = f"{self.base_url}/v2.1/films/{film_id}/sequels_and_prequels"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения сиквелов для {film_id}: {e}")
            return []

    def get_similar_films(self, film_id: int) -> Dict:
        """Похожие фильмы"""
        url = f"{self.base_url}/v2.2/films/{film_id}/similars"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения похожих фильмов {film_id}: {e}")
            return {"items": []}

    def get_film_videos(self, film_id: int) -> Dict:
        """Видео (трейлеры) к фильму"""
        url = f"{self.base_url}/v2.2/films/{film_id}/videos"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения видео {film_id}: {e}")
            return {"items": []}

    def get_film_reviews(self, film_id: int, page: int = 1) -> Dict:
        """Отзывы к фильму"""
        url = f"{self.base_url}/v2.2/films/{film_id}/reviews"
        params = {"page": page}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения отзывов {film_id}: {e}")
            return {"items": [], "total": 0}

    def get_films_by_filters(self, genre: Optional[int] = None,
                             year_from: Optional[int] = None,
                             year_to: Optional[int] = None,
                             rating_from: Optional[int] = None,
                             rating_to: Optional[int] = None,
                             page: int = 1) -> Dict:
        """Фильмы по фильтрам"""
        url = f"{self.base_url}/v2.2/films"
        params = {
            "genres": genre,
            "yearFrom": year_from,
            "yearTo": year_to,
            "ratingFrom": rating_from,
            "ratingTo": rating_to,
            "page": page,
            "order": "RATING"  # или YEAR, NUM_VOTE
        }
        # Удаляем None значения
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка фильтрации фильмов: {e}")
            return {"items": [], "total": 0}

    def get_top_films(self, page: int = 1) -> Dict:
        """Топ фильмов"""
        url = f"{self.base_url}/v2.2/films/top"
        params = {
            "type": "TOP_250_BEST_FILMS",
            "page": page
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения топа: {e}")
            return {"films": [], "pagesCount": 0}

# Глобальный экземпляр клиента
kinopoisk_client = KinopoiskClient()