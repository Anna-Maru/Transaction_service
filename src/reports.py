import pandas as pd
import datetime as dt
from typing import Optional, Callable
import functools
import os


def save_report(file_name: Optional[str] = None):
    """Декоратор для функций, формирующих отчёты."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            base_name = file_name or f"report_{func.__name__}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            path = os.path.join("data", base_name)

            if isinstance(result, pd.DataFrame):
                result.to_csv(path, index=False, encoding="utf-8-sig")
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(result))

            print(f"✅ Отчёт '{func.__name__}' сохранён в файл: {path}")
            return result

        return wrapper
    return decorator


@save_report()
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние 3 месяца."""
    if date:
        end_date = pd.to_datetime(date)
    else:
        end_date = pd.Timestamp.now()

    start_date = end_date - pd.DateOffset(months=3)

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    mask = (df["Дата операции"].between(start_date, end_date)) & (df["Категория"] == category)
    report = df.loc[mask, ["Дата операции", "Сумма операции", "Категория", "Описание"]]

    report = report[report["Сумма операции"] > 0]

    return report


@save_report("report_weekday.csv")
def spending_by_weekday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает средние траты в каждый день недели за последние 3 месяца."""
    if date:
        end_date = pd.to_datetime(date)
    else:
        end_date = pd.Timestamp.now()

    start_date = end_date - pd.DateOffset(months=3)

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    mask = df["Дата операции"].between(start_date, end_date)
    df = df.loc[mask, ["Дата операции", "Сумма операции"]]

    df["weekday"] = df["Дата операции"].dt.day_name(locale="ru_RU")  # день недели
    report = df.groupby("weekday", as_index=False)["Сумма операции"].mean()
    report.rename(columns={"Сумма операции": "Средние траты"}, inplace=True)

    return report
