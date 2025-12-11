import os
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TMDBClient:
    """TMDB API client with optional proxy support"""

    def __init__(self):
        self.api_key = os.getenv('TMDB_API_KEY')
        if not self.api_key:
            logger.error("TMDB_API_KEY is not set")
            raise ValueError("Please set TMDB_API_KEY in environment variables")

        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json"
        }

        # Optional proxy configuration
        self.proxies = {}
        http_proxy = os.getenv('HTTP_PROXY')
        if http_proxy:
            self.proxies = {'http': http_proxy, 'https': http_proxy}
            logger.info(f"Using proxy: {http_proxy}")

        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Set timeout
        self.timeout = 15

    def search_movies(self, query: str, year: Optional[str] = None,
                      media_type: Optional[str] = None) -> List[Dict]:
        """Search for movies and TV shows"""
        url = f"{self.base_url}/search/multi"
        params = {
            "query": query,
            "include_adult": False,
            "language": "ru-RU",
            "page": 1
        }

        if year:
            params["year"] = year

        try:
            response = self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            # Filter by media type if specified
            results = data.get("results", [])
            if media_type:
                results = [r for r in results if r.get('media_type') == media_type]

            return results[:10]

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching movies: {e}")
            return []

    def get_movie_details(self, movie_id: int, media_type: str = "movie") -> Dict:
        """Get movie/TV show details"""
        url = f"{self.base_url}/{media_type}/{movie_id}"
        params = {
            "language": "ru-RU",
            "append_to_response": "credits,videos"
        }

        try:
            response = self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting movie details: {e}")
            return {}

    def get_similar_movies(self, movie_id: int, media_type: str = "movie") -> List[Dict]:
        """Get similar movies/TV shows"""
        url = f"{self.base_url}/{media_type}/{movie_id}/similar"
        params = {"language": "ru-RU", "page": 1}

        try:
            response = self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:10]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting similar movies: {e}")
            return []

    def discover_movies(self, genre: Optional[str] = None,
                        year: Optional[str] = None,
                        sort_by: str = "popularity.desc") -> List[Dict]:
        """Discover movies by criteria"""
        # Map Russian genre names to TMDB genre IDs
        genre_map = {
            'детектив': 9648,
            'комедия': 35,
            'драма': 18,
            'фантастика': 878,
            'боевик': 28,
            'триллер': 53,
            'ужасы': 27,
            'мелодрама': 10749,
            'приключения': 12,
            'фэнтези': 14,
            'мультфильм': 16,
            'биография': 36,
            'вестерн': 37
        }

        url = f"{self.base_url}/discover/movie"
        params = {
            "language": "ru-RU",
            "sort_by": sort_by,
            "page": 1
        }

        if genre and genre.lower() in genre_map:
            params["with_genres"] = genre_map[genre.lower()]

        if year:
            params["primary_release_year"] = year

        try:
            response = self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:10]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error discovering movies: {e}")
            return []

    def get_tv_series_info(self, series_id: int) -> Dict:
        """Get TV series information"""
        url = f"{self.base_url}/tv/{series_id}"
        params = {"language": "ru-RU"}

        try:
            response = self.session.get(
                url,
                params=params,
                proxies=self.proxies,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting TV series info: {e}")
            return {}

# Global TMDB client instance
tmdb_client = TMDBClient()