import json
from datetime import datetime
from src.views import get_main_page_json


def main():
    """Основная функция запуска проекта"""

    print("===========================================")
    print("      💳 Transaction Service запущен       ")
    print("===========================================\n")

    # Пример использования - текущая дата
    date_str = "2020-05-20 14:30:00"

    print("Главная страница (пример JSON):")
    result = get_main_page_json(date_str)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n✅ Работа программы завершена.")


if __name__ == "__main__":
    main()
