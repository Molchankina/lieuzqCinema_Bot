# bot/movie_api.py

import logging
from typing import List, Dict
from .tmdb_client import tmdb_client
from .kinopoisk_client import kinopoisk_client

logger = logging.getLogger(__name__)

class MovieAPI:
    def __init__(self):
        self.use_tmdb = True  # По умолчанию используем TMDB

    def search(self, query: str) -> List[Dict]:
        """Поиск фильмов"""
        try:
            if self.use_tmdb and hasattr(tmdb_client, 'search_movies'):
                results = tmdb_client.search_movies(query)
                return self._format_tmdb_results(results)
            elif hasattr(kinopoisk_client, 'search_films'):
                result = kinopoisk_client.search_films(query)
                return self._format_kinopoisk_results(result)
            else:
                return []
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []

    def _format_tmdb_results(self, results: List[Dict]) -> List[Dict]:
        """Форматирование результатов TMDB"""
        formatted = []
        for item in results[:5]:
            formatted.append({
                'id': item.get('id'),
                'title': item.get('title') or item.get('name', ''),
                'year': (item.get('release_date') or item.get('first_air_date', ''))[:4],
                'rating': item.get('vote_average'),
                'poster_path': item.get('poster_path'),
                'media_type': item.get('media_type', 'movie'),
                'overview': item.get('overview', '')[:200] + '...' if item.get('overview') else ''
            })
        return formatted

    def _format_kinopoisk_results(self, result: Dict) -> List[Dict]:
        """Форматирование результатов КиноПоиска"""
        formatted = []
        films = result.get('films', [])

        for film in films[:5]:
            formatted.append({
                'id': film.get('filmId'),
                'title': film.get('nameRu', ''),
                'year': str(film.get('year', '')),
                'rating': film.get('rating'),
                'poster_path': film.get('posterUrlPreview'),
                'media_type': 'movie' if film.get('type') == 'FILM' else 'tv',
                'overview': film.get('description', '')[:200] + '...' if film.get('description') else ''
            })
        return formatted

# Глобальный экземпляр
movie_api = MovieAPI()