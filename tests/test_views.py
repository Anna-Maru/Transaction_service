import pytest
from unittest.mock import patch, Mock
from src.views import get_main_page_json


@pytest.fixture
def sample_transactions():
    return [
        {"карта": "1234567890123456", "сумма": 1200,
         "категория": "Продукты", "дата": "2025-05-05"},
        {"карта": "1234567890123456", "сумма": 800,
         "категория": "Транспорт", "дата": "2025-05-10"},
        {"карта": "9876543210987654", "сумма": 1500,
         "категория": "Развлечения", "дата": "2025-05-12"},]


@patch("src.views.load_user_settings")
@patch("src.views.requests.get")
def test_currencies_and_stocks(mock_get, mock_settings, sample_transactions):
    """Проверяем формирование данных по валютам и акциям,
    подменяя внешние API через mock."""


    mock_settings.return_value = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN"]
    }


    def mock_api_response(*args, **kwargs):
        url = args[0] if args else kwargs.get('url', '')

        mock_response = Mock()
        mock_response.raise_for_status = Mock()


        if "exchangerates_data/latest" in url and "AAPL" not in url:
            mock_response.json.return_value = {
                "rates": {"USD": 80.0, "EUR": 90.0}
            }

        elif "AAPL" in url:
            mock_response.json.return_value = {"price": 150.0}
        elif "AMZN" in url:
            mock_response.json.return_value = {"price": 3200.0}
        else:
            mock_response.json.return_value = {}

        return mock_response

    mock_get.side_effect = mock_api_response

    result = get_main_page_json("2025-05-20 12:00:00", sample_transactions)


    assert "currency_rates" in result
    assert result["currency_rates"]["USD"] == 80.0
    assert result["currency_rates"]["EUR"] == 90.0

    assert "stock_prices" in result
    assert result["stock_prices"]["AAPL"] == 150.0
    assert result["stock_prices"]["AMZN"] == 3200.0


    assert mock_get.call_count >= 3
