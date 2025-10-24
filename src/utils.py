import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = "https://api.apilayer.com/exchangerates_data/latest"
HEADERS = {"apikey": API_KEY}


def get_greeting(dt: datetime) -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_month_range(date: datetime) -> tuple:
    """Возвращает диапазон дат (начало месяца, указанная дата)."""
    start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_date, date


def load_user_settings(path: str = "user_settings.json") -> Dict[str, Any]:
    """Загружает пользовательские настройки валют и акций."""
    try:
        if not os.path.exists(path):
            logging.warning(f"Файл настроек {path} не найден. Возвращаем пустые настройки.")
            return {"user_currencies": [], "user_stocks": []}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при разборе JSON из {path}: {e}")
        return {"user_currencies": [], "user_stocks": []}
    except Exception as e:
        logging.error(f"Ошибка при загрузке настроек из {path}: {e}")
        return {"user_currencies": [], "user_stocks": []}


def get_currency_rates(currencies: List[str]) -> Dict[str, Any]:
    """Получает текущие курсы валют."""
    try:
        if not currencies:
            return {}

        if not API_KEY:
            logging.error("API_KEY не установлен")
            return {cur: None for cur in currencies}

        params = {"base": "USD", "symbols": ",".join(currencies)}
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "rates" not in data:
            logging.error(f"Неожиданный формат ответа API: {data}")
            return {cur: None for cur in currencies}

        rates = {cur: data["rates"].get(cur, None) for cur in currencies}
        return {k: v for k, v in rates.items() if v is not None}
    except requests.exceptions.Timeout:
        logging.error("Таймаут при получении курсов валют")
        return {cur: None for cur in currencies}
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса при получении курсов валют: {e}")
        return {cur: None for cur in currencies}
    except Exception as e:
        logging.error(f"Неожиданная ошибка при получении курсов валют: {e}")
        return {cur: None for cur in currencies}


def get_stock_prices(stocks: List[str]) -> Dict[str, Any]:
    """
    Получает текущие цены акций.

    Примечание: exchangerates_data API не поддерживает акции.
    Эта функция является заглушкой и требует интеграции с реальным API акций
    (например, Alpha Vantage, Yahoo Finance, Finnhub и т.д.)
    """
    prices = {}

    if not stocks:
        return prices

    logging.warning("get_stock_prices: https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}.")

    STOCK_API_URL = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}"
    for symbol in stocks:
        try:
            response = requests.get(f"{STOCK_API_URL}/{symbol}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            prices[symbol] = data.get("price", None)
        except Exception as e:
            logging.error(f"Ошибка при получении данных акции {symbol}: {e}")
            prices[symbol] = None

    return prices


def get_card_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возвращает статистику по каждой карте."""
    if df.empty:
        return []

    cards_info = []
    grouped = df.groupby("card_number")["amount"].sum().reset_index()

    for _, row in grouped.iterrows():
        card_tail = str(row["card_number"])[-4:]
        total = round(row["amount"], 2)
        cashback = round(total * 0.01, 2)
        cards_info.append({"card_last_digits": card_tail, "total_spent": total, "cashback": cashback})

    return cards_info


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ-N транзакций по сумме платежа."""
    if df.empty:
        return []

    top_df = df.nlargest(top_n, "amount")
    return top_df.to_dict(orient="records")
