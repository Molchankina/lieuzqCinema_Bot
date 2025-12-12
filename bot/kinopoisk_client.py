# bot/kinopoisk_client.py

import os
import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

class KinopoiskClient:
    def __init__(self):
        self.api_key = os.getenv('KINOPOISK_API_KEY')
        if not self.api_key:
            logger.warning("KINOPOISK_API_KEY не установлен")
            self.api_key = None

        self.base_url = "https://kinopoiskapiunofficial.tech/api"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    def search_films(self, query: str) -> Dict:
        """Поиск фильмов"""
        if not self.api_key:
            return {"films": []}

        url = f"{self.base_url}/v2.1/films/search-by-keyword"
        params = {"keyword": query, "page": 1}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка поиска КиноПоиск: {e}")
            return {"films": []}

# Глобальный экземпляр
kinopoisk_client = KinopoiskClient()