import pytest
import pandas as pd
from src.services import analyze_profitable_categories, investment_bank


@pytest.fixture
def sample_transactions_df():
    """Пример датафрейма с транзакциями для анализа кешбэка."""
    return pd.DataFrame(
        {
            "date": [
                "2025-05-01",
                "2025-05-10",
                "2025-05-20",
                "2025-06-05",
            ],
            "category": ["Продукты", "Транспорт", "Продукты", "Одежда"],
            "amount": [1500, 700, 2300, 1200],
        }
    )


def test_analyze_profitable_categories_valid(sample_transactions_df):
    """Проверяем корректность расчёта кешбэка по категориям."""
    result = analyze_profitable_categories(sample_transactions_df, 2025, 5)

    assert isinstance(result, dict)

    assert result.get("Продукты") == 38
    assert result.get("Транспорт") == 7

    assert "Одежда" not in result


def test_analyze_profitable_categories_empty_df():
    """Если на вход пустой DataFrame — возвращаем пустой результат."""
    df = pd.DataFrame(columns=["date", "category", "amount"])
    result = analyze_profitable_categories(df, 2025, 5)
    assert result == {}


def test_analyze_profitable_categories_invalid_data():
    """Если в данных ошибка — возвращается словарь с ключом 'error'."""
    bad_df = pd.DataFrame({"wrong": [1, 2, 3]})
    result = analyze_profitable_categories(bad_df, 2025, 5)
    assert "error" in result


@pytest.fixture
def sample_transactions_list():
    return [
        {"Дата операции": "2025-05-05", "Сумма операции": 1712},
        {"Дата операции": "2025-05-12", "Сумма операции": 803},
        {"Дата операции": "2025-05-25", "Сумма операции": 1000},
        {"Дата операции": "2025-06-01", "Сумма операции": 540},
    ]


@pytest.mark.parametrize(
    "limit,expected",
    [
        (50, (1750 - 1712) + (850 - 803) + (1000 - 1000)),
        (100, (1800 - 1712) + (900 - 803) + (1000 - 1000)),
    ],
)
def test_investment_bank_valid(sample_transactions_list, limit, expected):
    """Проверяем правильность расчёта округлений только для указанного месяца."""
    result = investment_bank("2025-05", sample_transactions_list, limit)
    assert isinstance(result, float)
    assert result == round(expected, 2)


def test_investment_bank_empty_transactions():
    """Если список транзакций пуст — возвращаем 0."""
    result = investment_bank("2025-05", [], 50)
    assert result == 0.0


def test_investment_bank_invalid_date_format():
    """Если неверный формат месяца, функция не падает."""
    result = investment_bank("2025/05", [], 50)
    assert result == 0.0
