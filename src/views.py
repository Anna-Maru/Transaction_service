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

logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_main_page_json(date_str: str, transactions_path: str | pd.DataFrame | list) -> Dict[str, Any]:
    """Возвращает JSON-ответ для страницы 'Главная'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start_date, end_date = get_month_range(dt)

        if isinstance(transactions_path, list):
            df = pd.DataFrame(transactions_path)
        elif isinstance(transactions_path, pd.DataFrame):
            df = transactions_path.copy()
        else:
            df = pd.read_excel(transactions_path)

        settings = load_user_settings()
        currencies = settings.get("user_currencies", [])
        stocks = settings.get("user_stocks", [])

        if df.empty:
            logging.warning("DataFrame транзакций пуст")
            return {
                "greeting": get_greeting(dt),
                "period": {"from": start_date.strftime("%Y-%m-%d"), "to": end_date.strftime("%Y-%m-%d")},
                "cards": [],
                "top_transactions": [],
                "currency_rates": get_currency_rates(currencies),
                "stock_prices": get_stock_prices(stocks),
            }

        rename_map = {
            "Дата операции": "date",
            "дата": "date",
            "Номер карты": "card_number",
            "карта": "card_number",
            "Сумма операции": "amount",
            "сумма": "amount",
            "Категория": "category",
            "категория": "category",
        }
        df = df.rename(columns={col: rename_map.get(col, col) for col in df.columns})

        required_columns = ["date", "card_number", "amount"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Отсутствуют необходимые колонки: {', '.join(missing_columns)}"
            logging.error(error_msg)
            return {"error": error_msg}

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        initial_count = len(df)
        df = df.dropna(subset=["date", "amount"])
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logging.warning(f"Удалено {dropped_count} строк с некорректными данными")

        mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        df_filtered = df.loc[mask].copy()

        if df_filtered.empty:
            logging.info(f"Нет транзакций за период {start_date} - {end_date}")

        response = {
            "greeting": get_greeting(dt),
            "period": {"from": start_date.strftime("%Y-%m-%d"), "to": end_date.strftime("%Y-%m-%d")},
            "cards": get_card_stats(df_filtered),
            "top_transactions": get_top_transactions(df_filtered),
            "currency_rates": get_currency_rates(currencies),
            "stock_prices": get_stock_prices(stocks),
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
