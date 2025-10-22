import os
import pandas as pd
import pytest
from src.reports import spending_by_category, spending_by_weekday


@pytest.fixture
def sample_transactions():
    """Создаёт тестовый датафрейм с транзакциями"""
    data = {
        "Дата операции": [
            "2025-07-01", "2025-08-15", "2025-09-10", "2025-09-20", "2025-10-01"
        ],
        "Сумма операции": [1200, 500, 2500, 800, 300],
        "Категория": ["Продукты", "Транспорт", "Продукты", "Кафе", "Продукты"],
        "Описание": ["Магазин", "Метро", "Супермаркет", "Starbucks", "Пятёрочка"]
    }
    return pd.DataFrame(data)


def test_spending_by_category_creates_file(tmp_path, sample_transactions, monkeypatch):
    """Проверяет, что функция создаёт CSV-файл и возвращает DataFrame"""
    monkeypatch.chdir(tmp_path)
    os.mkdir("data")

    df = spending_by_category(sample_transactions, "Продукты", date="2025-10-10")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Категория" in df.columns
    assert all(df["Категория"] == "Продукты")

    files = list((tmp_path / "data").glob("report_spending_by_category_*.csv"))
    assert len(files) == 1, "Файл отчёта не был создан"


def test_spending_by_weekday_creates_file(tmp_path, sample_transactions, monkeypatch):
    """Проверяет, что функция создаёт CSV-файл с фиксированным именем"""
    monkeypatch.chdir(tmp_path)
    os.mkdir("data")

    df = spending_by_weekday(sample_transactions, date="2025-10-10")

    assert isinstance(df, pd.DataFrame)
    assert "weekday" in df.columns
    assert "Средние траты" in df.columns
    assert not df.empty

    path = tmp_path / "data" / "report_weekday.csv"
    assert path.exists(), "Файл report_weekday.csv не был создан"
    assert path.stat().st_size > 0, "Файл отчёта пуст"
