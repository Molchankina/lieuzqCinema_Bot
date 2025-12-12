import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tmdb():
    """Тест TMDB API"""
    from bot.tmdb_client import tmdb_client

    logger.info(f"TMDB API Key: {'Есть' if tmdb_client.api_key else 'Нет'}")
    logger.info(f"TMDB Client активен: {tmdb_client.is_active}")

    if tmdb_client.is_active:
        logger.info("Тестируем поиск 'Матрица' через TMDB...")
        results = tmdb_client.search_movies('Матрица')
        logger.info(f"Результатов: {len(results)}")
        if results:
            logger.info(f"Первый результат: {results[0].get('title')}")
        return results
    return []

def test_kinopoisk():
    """Тест КиноПоиск API"""
    from bot.kinopoisk_client import kinopoisk_client

    logger.info(f"КиноПоиск API Key: {'Есть' if kinopoisk_client.api_key else 'Нет'}")

    if kinopoisk_client.api_key:
        logger.info("Тестируем поиск 'Матрица' через КиноПоиск...")
        result = kinopoisk_client.search_films('Матрица')
        results = result.get('films', [])
        logger.info(f"Результатов: {len(results)}")
        if results:
            logger.info(f"Первый результат: {results[0].get('nameRu')}")
        return results
    return []

def main():
    print("=" * 50)
    print("Тестирование API поиска фильмов")
    print("=" * 50)

    # Проверяем переменные окружения
    print("\n📋 Переменные окружения:")
    print(f"TMDB_API_KEY: {'***' + os.getenv('TMDB_API_KEY', 'НЕТ')[-4:] if os.getenv('TMDB_API_KEY') else 'НЕТ'}")
    print(f"KINOPOISK_API_KEY: {'***' + os.getenv('KINOPOISK_API_KEY', 'НЕТ')[-4:] if os.getenv('KINOPOISK_API_KEY') else 'НЕТ'}")
    print(f"USE_TMDB: {os.getenv('USE_TMDB', 'true')}")

    use_tmdb = os.getenv('USE_TMDB', 'true').lower() == 'true'

    if use_tmdb:
        print("\n🔍 Тестируем TMDB...")
        results = test_tmdb()
    else:
        print("\n🔍 Тестируем КиноПоиск...")
        results = test_kinopoisk()

    if results:
        print(f"\n✅ API работает! Найдено фильмов: {len(results)}")
    else:
        print("\n❌ API не вернул результатов. Возможные причины:")
        print("1. API ключ не установлен или неверный")
        print("2. Для TMDB в России нужен VPN/DNS")
        print("3. API сервис временно недоступен")
        print("4. Нет результатов по запросу")

if __name__ == '__main__':
    main()