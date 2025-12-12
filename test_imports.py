import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("Тестирование импортов MovieMate Bot")
print("=" * 50)

modules_to_test = [
    ("bot.handlers", "handlers"),
    ("bot.database", "database"),
    ("bot.tmdb_client", "tmdb_client"),
    ("bot.kinopoisk_client", "kinopoisk_client"),
    ("bot.db_utils", "db_utils"),
    ("bot.movie_api", "movie_api"),
]

all_ok = True

for module_name, display_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✅ {display_name} - ОК")
    except ImportError as e:
        print(f"❌ {display_name} - Ошибка: {e}")
        all_ok = False
    except Exception as e:
        print(f"⚠️  {display_name} - Другая ошибка: {e}")
        all_ok = False

print("=" * 50)
if all_ok:
    print("🎉 Все модули импортируются успешно!")
else:
    print("😔 Есть проблемы с импортами")

print("\nСодержимое папки 'bot':")
for item in os.listdir("bot"):
    print(f"  - {item}")