import os
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
from bot.kinopoisk_client import kinopoisk_client

logger = logging.getLogger(__name__)

class MovieAPI:
    """Универсальный API для работы с фильмами"""

    def __init__(self):
        self.use_vpn = os.getenv('USE_VPN', 'False').lower() == 'true'
        self.vpn_url = os.getenv('VPN_API_URL')
        self.proxy = os.getenv('HTTP_PROXY')

    def search(self, query: str, year: Optional[str] = None,
               media_type: Optional[str] = None) -> List[Dict]:
        """Поиск фильмов и сериалов"""
        result = kinopoisk_client.search_films(query)

        films = []
        for film in result.get('films', [])[:10]:
            # Преобразуем формат КиноПоиска в универсальный
            film_data = self._format_kinopoisk_film(film)

            # Фильтрация по году
            if year and film_data.get('year') != year:
                continue

            # Фильтрация по типу
            if media_type:
                kp_type = film.get('type', '').lower()
                if media_type == 'movie' and kp_type not in ['film', 'video']:
                    continue
                elif media_type == 'tv' and kp_type not in ['tv_series', 'mini_series']:
                    continue

            films.append(film_data)

        return films

    def get_details(self, film_id: int, media_type: Optional[str] = None) -> Dict:
        """Получение деталей фильма"""
        details = kinopoisk_client.get_film_details(film_id)

        if not details:
            return {}

        # Преобразуем в универсальный формат
        return self._format_kinopoisk_details(details)

    def get_similar(self, film_id: int, media_type: Optional[str] = None) -> List[Dict]:
        """Похожие фильмы"""
        result = kinopoisk_client.get_similar_films(film_id)

        films = []
        for film in result.get('items', [])[:10]:
            film_data = self._format_kinopoisk_film(film)
            films.append(film_data)

        return films

    def _format_kinopoisk_film(self, film: Dict) -> Dict:
        """Преобразование фильма КиноПоиска в универсальный формат"""
        kp_type = film.get('type', '').lower()

        # Определяем тип контента
        if kp_type in ['film', 'video', 'animated_film']:
            media_type = 'movie'
        elif kp_type in ['tv_series', 'mini_series', 'tv_show']:
            media_type = 'tv'
        else:
            media_type = 'movie'

        # Преобразуем год
        year = str(film.get('year', ''))[:4]

        return {
            'id': film.get('filmId') or film.get('kinopoiskId'),
            'title': film.get('nameRu', ''),
            'original_title': film.get('nameEn', '') or film.get('nameOriginal', ''),
            'year': year,
            'release_date': f"{year}-01-01" if year else None,
            'description': film.get('description', ''),
            'short_description': film.get('shortDescription', ''),
            'rating': film.get('ratingKinopoisk') or film.get('ratingImdb') or film.get('rating', ''),
            'votes': film.get('ratingKinopoiskVoteCount') or film.get('ratingImdbVoteCount', 0),
            'poster_url': film.get('posterUrlPreview') or film.get('posterUrl', ''),
            'genres': [g.get('genre', '') for g in film.get('genres', [])],
            'countries': [c.get('country', '') for c in film.get('countries', [])],
            'media_type': media_type,
            'kp_type': kp_type,
            'duration': film.get('filmLength'),
            'is_serial': kp_type in ['tv_series', 'mini_series']
        }

    def _format_kinopoisk_details(self, details: Dict) -> Dict:
        """Преобразование деталей фильма КиноПоиска"""
        kp_type = details.get('type', '').lower()

        if kp_type in ['film', 'video', 'animated_film']:
            media_type = 'movie'
        elif kp_type in ['tv_series', 'mini_series', 'tv_show']:
            media_type = 'tv'
        else:
            media_type = 'movie'

        year = str(details.get('year', ''))[:4]

        return {
            'id': details.get('kinopoiskId'),
            'title': details.get('nameRu', ''),
            'original_title': details.get('nameEn', '') or details.get('nameOriginal', ''),
            'year': year,
            'release_date': f"{year}-01-01" if year else None,
            'description': details.get('description', ''),
            'short_description': details.get('shortDescription', ''),
            'rating_kinopoisk': details.get('ratingKinopoisk'),
            'rating_imdb': details.get('ratingImdb'),
            'votes_kinopoisk': details.get('ratingKinopoiskVoteCount'),
            'votes_imdb': details.get('ratingImdbVoteCount'),
            'poster_url': details.get('posterUrl'),
            'poster_url_preview': details.get('posterUrlPreview'),
            'cover_url': details.get('coverUrl'),
            'logo_url': details.get('logoUrl'),
            'genres': [g.get('genre', '') for g in details.get('genres', [])],
            'countries': [c.get('country', '') for c in details.get('countries', [])],
            'duration': details.get('filmLength'),
            'media_type': media_type,
            'kp_type': kp_type,
            'serial': details.get('serial'),
            'short_film': details.get('shortFilm'),
            'completed': details.get('completed'),
            'has_imax': details.get('hasImax'),
            'has_3d': details.get('has3D'),
            'last_sync': details.get('lastSync'),
            'rating_age_limits': details.get('ratingAgeLimits'),
            'start_year': details.get('startYear'),
            'end_year': details.get('endYear'),
            'seasons': details.get('seasonsInfo', [])
        }

    def search_by_filters(self, genre: Optional[str] = None,
                          year: Optional[str] = None,
                          rating: Optional[float] = None,
                          sort_by: str = "rating") -> List[Dict]:
        """Поиск по фильтрам"""
        # Маппинг жанров (можно расширить)
        genre_map = {
            'детектив': 3,
            'комедия': 13,
            'драма': 17,
            'фантастика': 6,
            'боевик': 11,
            'триллер': 4,
            'ужасы': 7,
            'мелодрама': 22,
            'приключения': 12,
            'фэнтези': 14,
            'мультфильм': 16,
            'биография': 5,
            'вестерн': 10
        }

        genre_id = genre_map.get(genre.lower()) if genre else None
        year_int = int(year) if year and year.isdigit() else None

        result = kinopoisk_client.get_films_by_filters(
            genre=genre_id,
            year_from=year_int,
            year_to=year_int,
            rating_from=int(rating) if rating else None
        )

        films = []
        for film in result.get('items', [])[:10]:
            films.append(self._format_kinopoisk_film(film))

        return films

# Глобальный экземпляр API
movie_api = MovieAPI()