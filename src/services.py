import logging
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd


logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def analyze_profitable_categories(data: pd.DataFrame, year: int, month: int) -> Dict[str, float]:
    """Анализ выгодных категорий повышенного кешбэка за указанный месяц"""
    try:
        data["date"] = pd.to_datetime(data["date"])
        df_filtered = data[
            (data["date"].dt.year == year)
            & (data["date"].dt.month == month)
        ]

        category_sum = df_filtered.groupby("category")["amount"].sum()
        cashback_by_category = (category_sum // 100).astype(int).to_dict()

        logging.info(f"Выгодные категории за {year}-{month:02d} рассчитаны успешно")
        return cashback_by_category

    except Exception as e:
        logging.error(f"Ошибка в analyze_profitable_categories: {e}")
        return {"error": str(e)}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму, которую можно накопить в 'Инвесткопилке'
        за указанный месяц с заданным порогом округления."""
    try:
        target_month = datetime.strptime(month, "%Y-%m")

        total_saved = 0.0
        for t in transactions:
            date = datetime.strptime(t["Дата операции"], "%Y-%m-%d")
            if date.year == target_month.year and date.month == target_month.month:
                amount = float(t["Сумма операции"])
                rounded = ((amount // limit) + (1 if amount % limit != 0 else 0)) * limit
                saved = round(rounded - amount, 2)
                total_saved += saved

        total_saved = round(total_saved, 2)
        logging.info(f"Инвесткопилка за {month}: накоплено {total_saved} ₽ при шаге {limit}")
        return total_saved

    except Exception as e:
        logging.error(f"Ошибка в investment_bank: {e}")
        return 0.0
