import pandas as pd
from unittest.mock import patch
from src.views import get_main_page_json


@patch("src.views.get_currency_rates")
@patch("src.views.get_stock_prices")
@patch("src.views.get_card_stats")
@patch("src.views.get_top_transactions")
@patch("src.views.load_user_settings")
def test_get_main_page_json(
    mock_load_settings,
    mock_top_transactions,
    mock_card_stats,
    mock_stocks,
    mock_currencies,
    tmp_path
):
    """Интеграционный тест: проверяем, что функция корректно
    формирует JSON, обрабатывает Excel и вызывает все зависимые функции."""

    mock_load_settings.return_value = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN"],
    }
    mock_currencies.return_value = {"USD": 80, "EUR": 90}
    mock_stocks.return_value = {"AAPL": 150, "AMZN": 3200}
    mock_card_stats.return_value = [{"card_last_digits": "1234", "cashback": 5}]
    mock_top_transactions.return_value = [{"category": "Еда", "amount": 500}]


    df = pd.DataFrame({
        "Дата операции": ["2025-05-01", "2025-05-10"],
        "Номер карты": ["1234", "5678"],
        "Сумма операции": [100, 200],
        "Категория": ["Еда", "Транспорт"]
    })
    excel_path = tmp_path / "transactions.xlsx"
    df.to_excel(excel_path, index=False)

    result = get_main_page_json("2025-05-20 12:00:00", str(excel_path))

    assert isinstance(result, dict)
    assert "greeting" in result
    assert "period" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    assert result["currency_rates"]["USD"] == 80
    assert result["stock_prices"]["AAPL"] == 150
    assert result["cards"][0]["card_last_digits"] == "1234"
    assert result["top_transactions"][0]["category"] == "Еда"

    mock_load_settings.assert_called_once()
    mock_card_stats.assert_called_once()
    mock_top_transactions.assert_called_once()
    mock_currencies.assert_called_once_with(["USD", "EUR"])
    mock_stocks.assert_called_once_with(["AAPL", "AMZN"])
