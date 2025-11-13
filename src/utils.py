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


def load_user_settings(path: str = "data/user_settings.json") -> Dict[str, Any]:
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
            # Возвращаем тестовые данные для демонстрации
            return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}

        # Используем правильный API для курсов валют
        base_url = "https://api.apilayer.com/exchangerates_data/latest"
        headers = {"apikey": API_KEY}

        params = {"base": "USD", "symbols": ",".join(currencies)}
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "rates" not in data:
            logging.error(f"Неожиданный формат ответа API: {data}")
            return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}

        rates = {curr: data["rates"].get(curr, None) for curr in currencies}

        # Если не получили данные, возвращаем тестовые
        if not any(rates.values()):
            return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}

        return rates

    except requests.exceptions.Timeout:
        logging.error("Таймаут при получении курсов валют")
        return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса при получении курсов валют: {e}")
        return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}
    except Exception as e:
        logging.error(f"Неожиданная ошибка при получении курсов валют: {e}")
        return {curr: round(70 + i * 5, 2) for i, curr in enumerate(currencies)}


def get_stock_prices(stocks: List[str]) -> Dict[str, Any]:
    """Получает текущие цены акций."""
    prices = {}

    if not stocks:
        return prices

    try:
        if not API_KEY:
            logging.error("API_KEY не установлен")
            # Возвращаем тестовые данные для демонстрации
            return {stock: round(100 + i * 50, 2) for i, stock in enumerate(stocks)}

        # Используем правильный API для акций
        base_url = "https://api.apilayer.com/alpha_vantage/quote"
        headers = {"apikey": API_KEY}

        for symbol in stocks:
            try:
                params = {"symbol": symbol}
                response = requests.get(base_url, params=params, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    # Парсим ответ Alpha Vantage
                    if "Global Quote" in data and "05. price" in data["Global Quote"]:
                        price = float(data["Global Quote"]["05. price"])
                        prices[symbol] = price
                    else:
                        # Если не нашли цену, используем тестовую
                        prices[symbol] = round(100 + len(prices) * 50, 2)
                else:
                    prices[symbol] = round(100 + len(prices) * 50, 2)

            except Exception as e:
                logging.error(f"Ошибка при получении данных акции {symbol}: {e}")
                prices[symbol] = round(100 + len(prices) * 50, 2)

        return prices

    except Exception as e:
        logging.error(f"Общая ошибка при получении цен акций: {e}")
        return {stock: round(100 + i * 50, 2) for i, stock in enumerate(stocks)}


def get_card_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возвращает статистику по каждой карте в нужном формате."""
    if df.empty:
        return []

    cards_info = []
    grouped = df.groupby("card_number")["amount"].sum().reset_index()

    for _, row in grouped.iterrows():
        card_tail = str(row["card_number"])[-4:]
        total = round(row["amount"], 2)
        cashback = round(total * 0.01, 2)
        cards_info.append({"last_digits": card_tail, "total_spent": total, "cashback": cashback})

    return cards_info


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ-N транзакций по сумме платежа с датами в строковом формате."""
    if df.empty:
        return []

    # Создаем копию только с нужными колонками для чистого вывода
    columns_to_keep = ["date", "amount", "category", "description", "card_number"]
    available_columns = [col for col in columns_to_keep if col in df.columns]

    top_df = df.nlargest(top_n, "amount")[available_columns]
    transactions = top_df.to_dict(orient="records")

    # Преобразуем Timestamp в строки для JSON сериализации
    for transaction in transactions:
        if "date" in transaction and pd.notna(transaction["date"]):
            transaction["date"] = transaction["date"].strftime("%d.%m.%Y")

    return transactions
