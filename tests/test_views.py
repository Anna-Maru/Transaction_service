import pytest
import pandas as pd
from unittest.mock import patch

from src.views import get_main_page_json


class TestGetMainPageJson:
    """Тесты для функции get_main_page_json"""

    @pytest.fixture
    def sample_transactions_df(self):
        """Фикстура с тестовыми транзакциями"""
        return pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=10),
                "card_number": [
                    "*1234",
                    "*5678",
                    "*1234",
                    "*5678",
                    "*1234",
                    "*5678",
                    "*1234",
                    "*5678",
                    "*1234",
                    "*5678",
                ],
                "amount": [100, 200, 150, 250, 300, 350, 400, 450, 500, 550],
                "category": [
                    "Food",
                    "Transport",
                    "Food",
                    "Shopping",
                    "Food",
                    "Transport",
                    "Food",
                    "Shopping",
                    "Food",
                    "Transport",
                ],
            }
        )

    @pytest.fixture
    def sample_transactions_list(self):
        """Фикстура со списком транзакций"""
        return [
            {"date": "2024-01-01", "card_number": "*1234", "amount": 100, "category": "Food"},
            {"date": "2024-01-02", "card_number": "*5678", "amount": 200, "category": "Transport"},
            {"date": "2024-01-03", "card_number": "*1234", "amount": 150, "category": "Food"},
        ]

    @pytest.fixture
    def sample_settings(self):
        """Фикстура с пользовательскими настройками"""
        return {"user_currencies": ["EUR", "GBP"], "user_stocks": ["AAPL", "GOOGL"]}

    @pytest.fixture
    def mock_utils(self):
        """Мокирование функций из utils"""
        with (
            patch("src.views.get_greeting") as mock_greeting,
            patch("src.views.load_user_settings") as mock_settings,
            patch("src.views.get_currency_rates") as mock_currency,
            patch("src.views.get_stock_prices") as mock_stocks,
        ):
            mock_greeting.return_value = "Добрый день"
            mock_settings.return_value = {"user_currencies": ["EUR"], "user_stocks": ["AAPL"]}
            mock_currency.return_value = {"EUR": 0.85}
            mock_stocks.return_value = {"AAPL": None}

            yield {
                "greeting": mock_greeting,
                "settings": mock_settings,
                "currency": mock_currency,
                "stocks": mock_stocks,
            }

    def test_basic_functionality_with_dataframe(self, sample_transactions_df, mock_utils):
        """Базовый тест с DataFrame"""
        result = get_main_page_json("2024-01-15 14:30:00", sample_transactions_df)

        assert "error" not in result
        assert result["greeting"] == "Добрый день"
        assert "period" in result
        assert result["period"]["from"] == "2024-01-01"
        assert result["period"]["to"] == "2024-01-15"
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result

    def test_with_list_input(self, sample_transactions_list, mock_utils):
        """Тест с входными данными в виде списка"""
        result = get_main_page_json("2024-01-15 12:00:00", sample_transactions_list)

        assert "error" not in result
        assert isinstance(result["cards"], list)
        assert isinstance(result["top_transactions"], list)

    @patch("src.views.pd.read_excel")
    def test_with_file_path(self, mock_read_excel, sample_transactions_df, mock_utils):
        """Тест с путём к файлу Excel"""
        mock_read_excel.return_value = sample_transactions_df

        result = get_main_page_json("2024-01-15 12:00:00", "transactions.xlsx")

        mock_read_excel.assert_called_once_with("transactions.xlsx")
        assert "error" not in result

    @pytest.mark.parametrize(
        "date_str, expected_period",
        [
            ("2024-01-15 14:30:00", {"from": "2024-01-01", "to": "2024-01-15"}),
            ("2024-02-29 23:59:59", {"from": "2024-02-01", "to": "2024-02-29"}),
            ("2024-12-31 00:00:00", {"from": "2024-12-01", "to": "2024-12-31"}),
            ("2024-06-01 12:00:00", {"from": "2024-06-01", "to": "2024-06-01"}),
        ],
    )
    def test_date_ranges(self, date_str, expected_period, sample_transactions_df, mock_utils):
        """Проверка различных диапазонов дат"""
        result = get_main_page_json(date_str, sample_transactions_df)

        assert result["period"] == expected_period

    def test_empty_dataframe(self, mock_utils):
        """Тест с пустым DataFrame"""
        empty_df = pd.DataFrame(columns=["date", "card_number", "amount", "category"])

        result = get_main_page_json("2024-01-15 12:00:00", empty_df)

        assert "error" not in result
        assert result["cards"] == []
        assert result["top_transactions"] == []
        assert result["currency_rates"] == {"EUR": 0.85}
        assert result["stock_prices"] == {"AAPL": None}

    def test_column_renaming_cyrillic(self, mock_utils):
        """Проверка переименования колонок на кириллице"""
        df = pd.DataFrame(
            {
                "Дата операции": ["2024-01-01", "2024-01-02"],
                "Номер карты": ["*1234", "*5678"],
                "Сумма операции": [100, 200],
                "Категория": ["Food", "Transport"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) == 2

    def test_column_renaming_lowercase(self, mock_utils):
        """Проверка переименования колонок в нижнем регистре"""
        df = pd.DataFrame(
            {
                "дата": ["2024-01-01", "2024-01-02"],
                "карта": ["*1234", "*5678"],
                "сумма": [100, 200],
                "категория": ["Food", "Transport"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) == 2

    def test_missing_required_columns(self, mock_utils):
        """Тест с отсутствующими обязательными колонками"""
        df = pd.DataFrame({"date": ["2024-01-01"], "amount": [100]})

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" in result
        assert "card_number" in result["error"]

    def test_invalid_data_types(self, mock_utils):
        """Тест с некорректными типами данных"""
        df = pd.DataFrame(
            {
                "date": ["invalid_date", "2024-01-02", "2024-01-03"],
                "card_number": ["*1234", "*5678", "*9999"],
                "amount": ["not_a_number", 200, 300],
                "category": ["Food", "Transport", "Shopping"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) > 0

    def test_filtering_by_date_range(self, mock_utils):
        """Проверка фильтрации по периоду"""
        df = pd.DataFrame(
            {
                "date": ["2023-12-31", "2024-01-01", "2024-01-15", "2024-02-01"],
                "card_number": ["*1234", "*1234", "*1234", "*1234"],
                "amount": [100, 200, 300, 400],
                "category": ["A", "B", "C", "D"],
            }
        )

        result = get_main_page_json("2024-01-20 12:00:00", df)

        assert "error" not in result
        card = result["cards"][0]
        assert card["total_spent"] == 500.0

    def test_no_transactions_in_period(self, mock_utils):
        """Тест когда нет транзакций в указанном периоде"""
        df = pd.DataFrame(
            {
                "date": ["2023-12-31", "2024-02-01"],
                "card_number": ["*1234", "*5678"],
                "amount": [100, 200],
                "category": ["A", "B"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert result["cards"] == []
        assert result["top_transactions"] == []

    def test_invalid_date_format(self, sample_transactions_df, mock_utils):
        """Тест с некорректным форматом даты"""
        result = get_main_page_json("invalid-date", sample_transactions_df)

        assert "error" in result
        assert "Ошибка формата данных" in result["error"]

    @patch("src.views.pd.read_excel")
    def test_file_not_found(self, mock_read_excel, mock_utils):
        """Тест с несуществующим файлом"""
        mock_read_excel.side_effect = FileNotFoundError("File not found")

        result = get_main_page_json("2024-01-15 12:00:00", "nonexistent.xlsx")

        assert "error" in result
        assert "Файл не найден" in result["error"]

    def test_integration_with_card_stats(self, mock_utils):
        """Интеграционный тест с расчётом статистики карт"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "card_number": ["*1234", "*1234", "*5678"],
                "amount": [100, 150, 200],
                "category": ["A", "B", "C"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) == 2

        card_1234 = [c for c in result["cards"] if c["card_last_digits"] == "1234"][0]
        assert card_1234["total_spent"] == 250.0
        assert card_1234["cashback"] == 2.5

    def test_integration_with_top_transactions(self, mock_utils):
        """Интеграционный тест с топ транзакциями"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
                "card_number": ["*1234", "*5678", "*1234", "*5678"],
                "amount": [500, 300, 700, 400],
                "category": ["A", "B", "C", "D"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        assert len(result["top_transactions"]) == 4
        assert result["top_transactions"][0]["amount"] == 700
        assert result["top_transactions"][1]["amount"] == 500

    @pytest.mark.parametrize(
        "currencies, stocks",
        [
            (["EUR", "GBP"], ["AAPL"]),
            ([], []),
            (["USD"], ["GOOGL", "MSFT"]),
        ],
    )
    def test_user_settings_integration(self, currencies, stocks, sample_transactions_df):
        """Тест интеграции с пользовательскими настройками"""
        with (
            patch("src.views.load_user_settings") as mock_settings,
            patch("src.views.get_greeting") as mock_greeting,
            patch("src.views.get_currency_rates") as mock_currency,
            patch("src.views.get_stock_prices") as mock_stocks,
        ):
            mock_greeting.return_value = "Добрый день"
            mock_settings.return_value = {"user_currencies": currencies, "user_stocks": stocks}
            mock_currency.return_value = {cur: 0.85 for cur in currencies}
            mock_stocks.return_value = {stock: None for stock in stocks}

            result = get_main_page_json("2024-01-15 12:00:00", sample_transactions_df)

            mock_currency.assert_called_once_with(currencies)
            mock_stocks.assert_called_once_with(stocks)

            assert len(result["currency_rates"]) == len(currencies)
            assert len(result["stock_prices"]) == len(stocks)

    def test_greeting_time_variations(self, sample_transactions_df):
        """Проверка различных приветствий в зависимости от времени"""
        with (
            patch("src.views.load_user_settings") as mock_settings,
            patch("src.views.get_currency_rates") as mock_currency,
            patch("src.views.get_stock_prices") as mock_stocks,
        ):
            mock_settings.return_value = {"user_currencies": [], "user_stocks": []}
            mock_currency.return_value = {}
            mock_stocks.return_value = {}

            result_morning = get_main_page_json("2024-01-15 08:00:00", sample_transactions_df)
            assert result_morning["greeting"] == "Доброе утро"

            result_afternoon = get_main_page_json("2024-01-15 14:00:00", sample_transactions_df)
            assert result_afternoon["greeting"] == "Добрый день"

            result_evening = get_main_page_json("2024-01-15 19:00:00", sample_transactions_df)
            assert result_evening["greeting"] == "Добрый вечер"

            result_night = get_main_page_json("2024-01-15 01:00:00", sample_transactions_df)
            assert result_night["greeting"] == "Доброй ночи"

    def test_multiple_cards_statistics(self, mock_utils):
        """Тест статистики для множества карт"""
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=15),
                "card_number": ["*1111", "*2222", "*3333"] * 5,
                "amount": [100, 200, 300] * 5,
                "category": ["A"] * 15,
            }
        )

        result = get_main_page_json("2024-01-20 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) == 3

        totals = {card["card_last_digits"]: card["total_spent"] for card in result["cards"]}
        assert totals["1111"] == 500.0
        assert totals["2222"] == 1000.0
        assert totals["3333"] == 1500.0

    def test_edge_case_single_transaction(self, mock_utils):
        """Тест с одной транзакцией"""
        df = pd.DataFrame({"date": ["2024-01-15"], "card_number": ["*9999"], "amount": [999.99], "category": ["Test"]})

        result = get_main_page_json("2024-01-20 12:00:00", df)

        assert "error" not in result
        assert len(result["cards"]) == 1
        assert result["cards"][0]["total_spent"] == 999.99
        assert result["cards"][0]["cashback"] == 10.0
        assert len(result["top_transactions"]) == 1

    def test_large_amounts(self, mock_utils):
        """Тест с большими суммами"""
        df = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "card_number": ["*1234", "*1234"],
                "amount": [999999.99, 1000000.00],
                "category": ["A", "B"],
            }
        )

        result = get_main_page_json("2024-01-15 12:00:00", df)

        assert "error" not in result
        card = result["cards"][0]
        assert card["total_spent"] == 1999999.99
        assert card["cashback"] == 20000.0
