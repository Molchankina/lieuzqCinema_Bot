# test_api_fixed.py в корне проекта

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tmdb_search():
    """Тестируем поиск через TMDB"""
    print("\n🔍 Тестируем TMDB поиск...")

    from bot.tmdb_client import tmdb_client

    # Проверяем статус
    print(f"TMDB активен: {tmdb_client.is_active}")
    print(f"TMDB API Key: {'Есть' if tmdb_client.api_key else 'Нет'}")

    if tmdb_client.is_active:
        # Тестовый запрос
        print("Ищу 'Матрица'...")
        results = tmdb_client.search_movies("Матрица")
        print(f"Найдено результатов: {len(results)}")

        if results:
            print("\nПервый результат:")
            movie = results[0]
            print(f"  Название: {movie.get('title') or movie.get('name')}")
            print(f"  Год: {(movie.get('release_date') or movie.get('first_air_date', ''))[:4]}")
            print(f"  Тип: {movie.get('media_type')}")
            return True
        else:
            print("⚠️ Нет результатов. Возможные причины:")
            print("  1. TMDB заблокирован в России")
            print("  2. Нужен VPN или настройка DNS на Railway")
            print("  3. API ключ неверный")
    else:
        print("❌ TMDB не активен. Установите TMDB_API_KEY в .env файле")

    return False

def test_kinopoisk_search():
    """Тестируем поиск через КиноПоиск"""
    print("\n🔍 Тестируем КиноПоиск поиск...")

    from bot.kinopoisk_client import kinopoisk_client

    # Проверяем статус
    print(f"КиноПоиск активен: {kinopoisk_client.is_active}")
    print(f"КиноПоиск API Key: {'Есть' if kinopoisk_client.api_key else 'Нет'}")

    if kinopoisk_client.is_active:
        # Тестовый запрос
        print("Ищу 'Матрица'...")
        result = kinopoisk_client.search_films("Матрица")
        films = result.get('films', [])
        print(f"Найдено результатов: {len(films)}")

        if films:
            print("\nПервый результат:")
            film = films[0]
            print(f"  Название: {film.get('nameRu')}")
            print(f"  Год: {film.get('year')}")
            print(f"  Рейтинг: {film.get('rating')}")
            return True
        else:
            print("⚠️ Нет результатов. Возможные причины:")
            print("  1. API ключ неверный")
            print("  2. Лимит запросов исчерпан (500 в день бесплатно)")
            print("  3. Сервис временно недоступен")
    else:
        print("❌ КиноПоиск не активен. Установите KINOPOISK_API_KEY в .env файле")

    return False

def main():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ API ПОСЛЕ ИСПРАВЛЕНИЯ ОШИБОК")
    print("=" * 50)

    # Читаем настройки
    use_tmdb = os.getenv('USE_TMDB', 'true').lower() == 'true'

    if use_tmdb:
        success = test_tmdb_search()
    else:
        success = test_kinopoisk_search()

    print("\n" + "=" * 50)
    if success:
        print("✅ API работает корректно!")
        print("   Бот должен искать фильмы.")
    else:
        print("❌ API не работает.")
        print("\n📋 РЕКОМЕНДАЦИИ:")

        if use_tmdb:
            print("1. Для TMDB в России:")
            print("   а) Используйте КиноПоиск (измените USE_TMDB=false в .env)")
            print("   б) Или настройте DNS на Railway:")
            print("      - Добавьте переменную DNS_SERVER=1.1.1.1")
            print("      - Перезапустите приложение")
        else:
            print("1. Для КиноПоиска:")
            print("   а) Получите ключ на kinopoiskapiunofficial.tech")
            print("   б) Убедитесь, что ключ правильный")
            print("   в) Проверьте лимит запросов (500/день)")

        print("\n2. Временное решение:")
        print("   Используйте фиктивные данные для тестирования бота")

if __name__ == '__main__':
    main()