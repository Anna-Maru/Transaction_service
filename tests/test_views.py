import pytest
from unittest.mock import patch
from src.views import get_main_page_json


@pytest.fixture
def sample_transactions():
    return [
        {"карта": "1234567890123456", "сумма": 1200, "категория": "Продукты", "дата": "2025-05-05"},
        {"карта": "1234567890123456", "сумма": 800, "категория": "Транспорт", "дата": "2025-05-10"},
        {"карта": "9876543210987654", "сумма": 1500, "категория": "Развлечения", "дата": "2025-05-12"},
    ]


@patch("src.views.requests.get")
def test_currencies_and_stocks(mock_get, sample_transactions):
    """Проверяем формирование данных по валютам и акциям,
    подменяя внешние API через mock."""
    mock_get.return_value.json.side_effect = [{"USD": 80, "EUR": 90}, {"AAPL": 150, "AMZN": 3200}]

    result = get_main_page_json("2025-05-20 12:00:00", sample_transactions)

    assert "currencies" in result
    assert result["currencies"]["USD"] == 80
    assert result["currencies"]["EUR"] == 90

    assert "stocks" in result
    assert result["stocks"]["AAPL"] == 150
    assert result["stocks"]["AMZN"] == 3200
    assert mock_get.call_count == 2
