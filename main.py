import json
from datetime import datetime
from pathlib import Path
from src.utils import (
    get_greeting,
    load_user_settings,
    get_currency_rates,
    get_stock_prices,
    get_card_stats,
    get_top_transactions,
)
from src.views import get_main_page_json
from config import FILE_JSON, FILE_XLSX

def main():
    """Основная функция запуска проекта"""

    print("===========================================")
    print("      💳 Transaction Service запущен       ")
    print("===========================================\n")

    now = datetime.now()
    greeting = get_greeting(now)
    print(f"{greeting}! Сегодня: {now.strftime('%d.%m.%Y %H:%M')}\n")

    #settings_path = Path(FILE_JSON)
    user_settings = load_user_settings(FILE_JSON)
    print("Настройки пользователя:")
    print(json.dumps(user_settings, indent=4, ensure_ascii=False))
    print()

    currencies = user_settings.get("user_currencies", ["USD", "EUR"])
    currency_rates = get_currency_rates(currencies)
    print("Текущие курсы валют:")
    for cur, rate in currency_rates.items():
        print(f"  {cur}: {rate}")
    print()

    stocks = user_settings.get("user_stocks", ["AAPL", "MSFT"])
    stock_prices = get_stock_prices(stocks)
    print("Текущие цены акций:")
    for stock, price in stock_prices.items():
        print(f"  {stock}: {price}")
    print()

    from pandas import DataFrame

    transactions = [
        {"card_number": "*1234", "amount": 150.0, "description": "Покупка продуктов"},
        {"card_number": "*5678", "amount": 2300.0, "description": "Онлайн-покупка"},
        {"card_number": "*1234", "amount": 450.0, "description": "Кафе"},
        {"card_number": "*5678", "amount": 700.0, "description": "Такси"},
    ]

    df = DataFrame(transactions)

    card_stats = get_card_stats(df)
    print("Статистика по картам:")
    for card in card_stats:
        print(
            f"  • Карта *{card['card_last_digits']}: "
            f"потрачено {card['total_spent']} ₽, кешбэк {card['cashback']} ₽"
        )
    print()

    top_transactions = get_top_transactions(df, top_n=3)
    print("Топ-3 транзакций:")
    for tr in top_transactions:
        print(f"  • {tr['amount']} ₽ — {tr.get('description', 'Без описания')}")
    print()

    print("Главная страница (пример JSON):")
    print(json.dumps(get_main_page_json(), indent=4, ensure_ascii=False))
    print("\n✅ Работа программы завершена.")


if __name__ == "__main__":
    main()
