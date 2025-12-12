import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_kinopoisk():
    """Тестируем подключение к КиноПоиску"""
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К КИНОПОИСКУ")
    print("=" * 60)

    # Проверяем переменные окружения
    api_key = os.getenv('KINOPOISK_API_KEY')
    print(f"📋 KINOPOISK_API_KEY: {'***' + api_key[-4:] if api_key else 'НЕТ'}")

    if not api_key or 'ваш_ключ' in api_key:
        print("❌ ОШИБКА: API ключ не установлен!")
        print("\n🔧 РЕШЕНИЕ:")
        print("1. Получите ключ на https://kinopoiskapiunofficial.tech")
        print("2. Добавьте в .env файл: KINOPOISK_API_KEY=ваш_ключ")
        return False

    # Тестируем подключение
    import requests

    url = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    params = {"keyword": "Матрица", "page": 1}

    print(f"\n🔗 Подключаюсь к: {url}")
    print(f"📝 Заголовки: {headers}")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📡 Статус ответа: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            films_count = data.get("searchFilmsCountResult", 0)
            print(f"✅ УСПЕХ! Найдено фильмов: {films_count}")

            if films_count > 0:
                film = data['films'][0]
                print(f"\n🎬 ПЕРВЫЙ ФИЛЬМ:")
                print(f"   Название: {film.get('nameRu')}")
                print(f"   Год: {film.get('year')}")
                print(f"   Рейтинг: {film.get('rating')}")

            return True

        elif response.status_code == 401:
            print("❌ ОШИБКА 401: Неверный API ключ!")
            print("   Получите новый ключ на сайте")
            return False

        else:
            print(f"❌ ОШИБКА {response.status_code}: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
        return False

if __name__ == '__main__':
    # Загружаем .env
    from dotenv import load_dotenv
    load_dotenv()

    test_kinopoisk()