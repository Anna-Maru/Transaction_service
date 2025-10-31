import logging
from datetime import datetime
from typing import Dict, Any
import pandas as pd

from src.utils import (
    get_greeting,
    get_month_range,
    load_user_settings,
    get_card_stats,
    get_top_transactions,
    get_currency_rates,
    get_stock_prices,
)
from config import FILE_XLSX

logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_main_page_json(date_str: str) -> Dict[str, Any]:
    """Возвращает JSON-ответ для страницы 'Главная'."""
    try:
        # Парсим дату из строки
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_date, end_date = get_month_range(dt)

        # Загружаем данные из Excel файла
        df = pd.read_excel(FILE_XLSX)

        # Загружаем настройки пользователя
        settings = load_user_settings()
        currencies = settings.get("user_currencies", [])
        stocks = settings.get("user_stocks", [])

        if df.empty:
            logging.warning("DataFrame транзакций пуст")
            return {
                "greeting": get_greeting(dt),
                "cards": [],
                "top_transactions": [],
                "currency_rates": [],
                "stock_prices": [],
            }

        # Переименовываем колонки для единообразия
        rename_map = {
            "Дата операции": "date",
            "дата": "date",
            "Номер карты": "card_number",
            "карта": "card_number",
            "Сумма операции": "amount",
            "сумма": "amount",
            "Категория": "category",
            "категория": "category",
            "Описание": "description",
            "описание": "description",
        }
        df = df.rename(columns={col: rename_map.get(col, col) for col in df.columns})

        # Проверяем обязательные колонки
        required_columns = ["date", "card_number", "amount"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Отсутствуют необходимые колонки: {', '.join(missing_columns)}"
            logging.error(error_msg)
            return {"error": error_msg}

        # Преобразуем типы данных - улучшенная обработка дат
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        # Удаляем строки с некорректными данными
        initial_count = len(df)
        df = df.dropna(subset=["date", "amount"])
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logging.warning(f"Удалено {dropped_count} строк с некорректными данными")

        # Фильтруем по периоду (с 1-го числа месяца по указанную дату)
        mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        df_filtered = df.loc[mask].copy()

        if df_filtered.empty:
            logging.info(f"Нет транзакций за период {start_date} - {end_date}")

        # Получаем курсы валют и цены акций
        currency_rates_dict = get_currency_rates(currencies)
        stock_prices_dict = get_stock_prices(stocks)

        # Формируем ответ в нужном формате
        response = {
            "greeting": get_greeting(dt),
            "cards": get_card_stats(df_filtered),
            "top_transactions": get_top_transactions(df_filtered, top_n=5),
            "currency_rates": [
                {"currency": curr, "rate": rate}
                for curr, rate in currency_rates_dict.items()
                if rate is not None
            ],
            "stock_prices": [
                {"stock": stock, "price": price}
                for stock, price in stock_prices_dict.items()
                if price is not None
            ]
        }

        logging.info("JSON для главной страницы успешно сформирован")
        return response

    except ValueError as e:
        error_msg = f"Ошибка формата данных: {e}"
        logging.error(error_msg)
        return {"error": error_msg}
    except FileNotFoundError as e:
        error_msg = f"Файл не найден: {e}"
        logging.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Неожиданная ошибка при формировании главной страницы: {type(e).__name__}: {e}"
        logging.error(error_msg)
        return {"error": error_msg}
