import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("ПРОВЕРКА ФУНКЦИЙ В handlers.py")
print("=" * 60)

try:
    from bot import handlers

    # Все функции, которые нужны main.py
    required = {
        'start': '✅',
        'help_command': '✅',
        'search_command': '✅',
        'show_top250': '✅',
        'random_real_movie': '✅',  # КРИТИЧЕСКИ ВАЖНО!
        'show_watchlist': '✅',
        'handle_message': '✅',
        'button_handler': '✅'
    }

    all_ok = True

    for func_name, status in required.items():
        if hasattr(handlers, func_name):
            print(f"{status} {func_name}")
        else:
            print(f"❌ {func_name} - НЕ НАЙДЕН!")
            all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ВСЕ функции на месте! Бот должен запуститься.")
    else:
        print("❌ Не все функции найдены. Исправьте handlers.py")

except ImportError as e:
    print(f"❌ Не могу импортировать handlers: {e}")