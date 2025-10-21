import json
import logging
from datetime import datetime
import pandas as pd
import requests
from typing import Dict, Any, List


logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


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
    start_date = date.replace(day=1, hour=0, minute=0, second=0)
    return start_date, date


def load_user_settings(path: str = "user_settings.json") -> Dict[str, Any]:
    """Загружает пользовательские настройки валют и акций."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_currency_rates(currencies: List[str]) -> dict[str, None] | dict[str, Any]:
    """Получает текущие курсы валют"""
    try:
        response = requests.get("URL_ДЛЯ_API_ВАЛЮТ")
        response.raise_for_status()
        data = response.json()
        rates = {cur: data["rates"].get(cur, None) for cur in currencies}
        return {k: v for k, v in rates.items() if v is not None}
    except Exception as e:
        logging.error(f"Ошибка при получении курсов валют: {e}")
        return {cur: None for cur in currencies}


def get_stock_prices(stocks: List[str]) -> Dict[str, float]:
    """Получает текущие цены акций S&P500."""
    prices = {}
    for symbol in stocks:
        try:
            response = requests.get(f"URL_ДЛЯ_API_АКЦИЙ/{symbol}")
            response.raise_for_status()
            data = response.json()
            prices[symbol] = data.get("price", None)
        except Exception as e:
            logging.error(f"Ошибка при получении данных акции {symbol}: {e}")
            prices[symbol] = None
    return prices


def get_card_stats(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возвращает статистику по каждой карте"""
    cards_info = []
    grouped = df.groupby("card_number")["amount"].sum().reset_index()

    for _, row in grouped.iterrows():
        card_tail = str(row["card_number"])[-4:]
        total = round(row["amount"], 2)
        cashback = round(total // 100, 2)
        cards_info.append({
            "card_last_digits": card_tail,
            "total_spent": total,
            "cashback": cashback
        })

    return cards_info


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ-N транзакций по сумме платежа."""
    top_df = df.nlargest(top_n, "amount")
    return top_df.to_dict(orient="records")


def get_main_page_json(date_str: str, transactions_path: str) -> Dict[str, Any]:
    """Возвращает JSON-ответ для страницы 'Главная' по следующим параметрам:
        date_str — строка с датой в формате 'YYYY-MM-DD HH:MM:SS'
        transactions_path — путь к Excel-файлу с транзакциями"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        start_date, end_date = get_month_range(dt)

        df = pd.read_excel(transactions_path)
        df["date"] = pd.to_datetime(df["date"])

        mask = (df["date"] >= start_date) & (df["date"] <= end_date)
        df_filtered = df.loc[mask]

        settings = load_user_settings()
        currencies = settings.get("user_currencies", [])
        stocks = settings.get("user_stocks", [])

        response = {
            "greeting": get_greeting(dt),
            "period": {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            },
            "cards": get_card_stats(df_filtered),
            "top_transactions": get_top_transactions(df_filtered),
            "currency_rates": get_currency_rates(currencies),
            "stock_prices": get_stock_prices(stocks)
        }

        logging.info("JSON для главной страницы успешно сформирован")
        return response

    except Exception as e:
        logging.error(f"Ошибка при формировании главной страницы: {e}")

        return {"error": str(e)}
