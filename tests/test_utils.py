import pytest
import pandas as pd
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import requests

from src.utils import (
    get_greeting,
    get_month_range,
    load_user_settings,
    get_currency_rates,
    get_stock_prices,
    get_card_stats,
    get_top_transactions,
)


class TestGetGreeting:
    """Тесты для функции get_greeting"""

    @pytest.mark.parametrize(
        "hour, expected",
        [
            (5, "Доброе утро"),
            (8, "Доброе утро"),
            (11, "Доброе утро"),
            (12, "Добрый день"),
            (14, "Добрый день"),
            (16, "Добрый день"),
            (17, "Добрый вечер"),
            (20, "Добрый вечер"),
            (22, "Добрый вечер"),
            (23, "Доброй ночи"),
            (0, "Доброй ночи"),
            (3, "Доброй ночи"),
            (4, "Доброй ночи"),
        ],
    )
    def test_greeting_by_hour(self, hour, expected):
        """Проверка приветствий в зависимости от времени суток"""
        dt = datetime(2024, 1, 1, hour, 0, 0)
        assert get_greeting(dt) == expected


class TestGetMonthRange:
    """Тесты для функции get_month_range"""

    @pytest.mark.parametrize(
        "date_str, expected_start, expected_end",
        [
            ("2024-01-15 14:30:45", "2024-01-01 00:00:00", "2024-01-15 14:30:45"),
            ("2024-02-29 23:59:59", "2024-02-01 00:00:00", "2024-02-29 23:59:59"),
            ("2024-12-31 12:00:00", "2024-12-01 00:00:00", "2024-12-31 12:00:00"),
            ("2024-06-01 00:00:00", "2024-06-01 00:00:00", "2024-06-01 00:00:00"),
        ],
    )
    def test_month_range(self, date_str, expected_start, expected_end):
        """Проверка корректности диапазона месяца"""
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        start, end = get_month_range(dt)

        expected_start_dt = datetime.strptime(expected_start, "%Y-%m-%d %H:%M:%S")
        expected_end_dt = datetime.strptime(expected_end, "%Y-%m-%d %H:%M:%S")

        assert start == expected_start_dt
        assert end == expected_end_dt

    def test_month_range_preserves_microseconds(self):
        """Проверка, что микросекунды сбрасываются"""
        dt = datetime(2024, 1, 15, 14, 30, 45, 123456)
        start, end = get_month_range(dt)
        assert start.microsecond == 0
        assert end.microsecond == 123456


class TestLoadUserSettings:
    """Тесты для функции load_user_settings"""

    def test_load_existing_file(self, tmp_path):
        """Загрузка существующего файла с настройками"""
        settings_file = tmp_path / "user_settings.json"
        test_data = {"user_currencies": ["EUR", "GBP"], "user_stocks": ["AAPL", "GOOGL"]}
        settings_file.write_text(json.dumps(test_data), encoding="utf-8")

        result = load_user_settings(str(settings_file))
        assert result == test_data

    def test_load_nonexistent_file(self):
        """Попытка загрузки несуществующего файла"""
        result = load_user_settings("nonexistent_file.json")
        assert result == {"user_currencies": [], "user_stocks": []}

    def test_load_invalid_json(self, tmp_path):
        """Загрузка файла с невалидным JSON"""
        settings_file = tmp_path / "invalid.json"
        settings_file.write_text("not a valid json{", encoding="utf-8")

        result = load_user_settings(str(settings_file))
        assert result == {"user_currencies": [], "user_stocks": []}

    def test_load_empty_file(self, tmp_path):
        """Загрузка пустого файла"""
        settings_file = tmp_path / "empty.json"
        settings_file.write_text("", encoding="utf-8")

        result = load_user_settings(str(settings_file))
        assert result == {"user_currencies": [], "user_stocks": []}


class TestGetCurrencyRates:
    """Тесты для функции get_currency_rates"""

    @pytest.mark.parametrize(
        "currencies, api_response, expected",
        [
            (["EUR", "GBP"], {"rates": {"EUR": 0.85, "GBP": 0.73}}, {"EUR": 0.85, "GBP": 0.73}),
            (["USD", "JPY"], {"rates": {"USD": 1.0, "JPY": 110.5}}, {"USD": 1.0, "JPY": 110.5}),
            ([], {}, {}),
        ],
    )
    @patch("utils.requests.get")
    @patch.dict(os.environ, {"API_KEY": "test_api_key"})
    def test_get_currency_rates_success(self, mock_get, currencies, api_response, expected):
        """Успешное получение курсов валют"""
        mock_response = MagicMock()
        mock_response.json.return_value = api_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        if currencies:
            result = get_currency_rates(currencies)
            assert result == expected
        else:
            result = get_currency_rates(currencies)
            assert result == {}

    @patch("utils.requests.get")
    @patch.dict(os.environ, {"API_KEY": "test_api_key"})
    def test_get_currency_rates_partial_data(self, mock_get):
        """Получение данных только для части валют"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {"EUR": 0.85}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_currency_rates(["EUR", "GBP"])
        assert result == {"EUR": 0.85}

    @patch("utils.requests.get")
    @patch.dict(os.environ, {"API_KEY": "test_api_key"})
    def test_get_currency_rates_timeout(self, mock_get):
        """Обработка таймаута при запросе"""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = get_currency_rates(["EUR", "GBP"])
        assert result == {"EUR": None, "GBP": None}

    @patch("utils.requests.get")
    @patch.dict(os.environ, {"API_KEY": "test_api_key"})
    def test_get_currency_rates_request_exception(self, mock_get):
        """Обработка ошибки запроса"""
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        result = get_currency_rates(["EUR"])
        assert result == {"EUR": None}

    @patch.dict(os.environ, {}, clear=True)
    def test_get_currency_rates_no_api_key(self):
        """Отсутствие API ключа"""
        result = get_currency_rates(["EUR"])
        assert result == {"EUR": None}

    @patch("utils.requests.get")
    @patch.dict(os.environ, {"API_KEY": "test_api_key"})
    def test_get_currency_rates_invalid_response_format(self, mock_get):
        """Неожиданный формат ответа API"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "format"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = get_currency_rates(["EUR"])
        assert result == {"EUR": None}


class TestGetStockPrices:
    """Тесты для функции get_stock_prices"""

    def test_get_stock_prices_empty_list(self):
        """Запрос без акций"""
        result = get_stock_prices([])
        assert result == {}

    @pytest.mark.parametrize(
        "stocks",
        [
            (["AAPL"]),
            (["AAPL", "GOOGL", "MSFT"]),
            (["TSLA", "AMZN"]),
        ],
    )
    def test_get_stock_prices_returns_none(self, stocks):
        """Функция возвращает None для всех акций (заглушка)"""
        result = get_stock_prices(stocks)
        assert all(value is None for value in result.values())
        assert set(result.keys()) == set(stocks)


class TestGetCardStats:
    """Тесты для функции get_card_stats"""

    def test_card_stats_empty_dataframe(self):
        """Статистика для пустого DataFrame"""
        df = pd.DataFrame(columns=["card_number", "amount"])
        result = get_card_stats(df)
        assert result == []

    @pytest.mark.parametrize(
        "transactions, expected",
        [
            (
                [
                    {"card_number": "*7197", "amount": 100.0},
                    {"card_number": "*7197", "amount": 50.0},
                ],
                [{"card_last_digits": "7197", "total_spent": 150.0, "cashback": 1.5}],
            ),
            (
                [
                    {"card_number": "*1234", "amount": 1000.0},
                    {"card_number": "*5678", "amount": 500.0},
                ],
                [
                    {"card_last_digits": "1234", "total_spent": 1000.0, "cashback": 10.0},
                    {"card_last_digits": "5678", "total_spent": 500.0, "cashback": 5.0},
                ],
            ),
            (
                [
                    {"card_number": "*9999", "amount": 99.99},
                ],
                [{"card_last_digits": "9999", "total_spent": 99.99, "cashback": 1.0}],
            ),
        ],
    )
    def test_card_stats_calculations(self, transactions, expected):
        """Проверка корректности расчётов статистики"""
        df = pd.DataFrame(transactions)
        result = get_card_stats(df)

        # Сортируем для корректного сравнения
        result_sorted = sorted(result, key=lambda x: x["card_last_digits"])
        expected_sorted = sorted(expected, key=lambda x: x["card_last_digits"])

        assert result_sorted == expected_sorted

    def test_card_stats_multiple_transactions(self):
        """Множество транзакций по разным картам"""
        df = pd.DataFrame(
            {"card_number": ["*1111", "*2222", "*1111", "*3333", "*2222"], "amount": [100, 200, 150, 300, 50]}
        )

        result = get_card_stats(df)
        assert len(result) == 3

        # Проверяем суммы
        totals = {item["card_last_digits"]: item["total_spent"] for item in result}
        assert totals["1111"] == 250.0
        assert totals["2222"] == 250.0
        assert totals["3333"] == 300.0


class TestGetTopTransactions:
    """Тесты для функции get_top_transactions"""

    def test_top_transactions_empty_dataframe(self):
        """Топ транзакций для пустого DataFrame"""
        df = pd.DataFrame(columns=["amount"])
        result = get_top_transactions(df)
        assert result == []

    def test_top_transactions_less_than_top_n(self):
        """Транзакций меньше, чем запрошено"""
        df = pd.DataFrame({"amount": [100, 200, 50], "description": ["A", "B", "C"]})

        result = get_top_transactions(df, top_n=5)
        assert len(result) == 3
        assert result[0]["amount"] == 200
        assert result[1]["amount"] == 100
        assert result[2]["amount"] == 50

    @pytest.mark.parametrize("top_n", [1, 3, 5, 10])
    def test_top_transactions_various_limits(self, top_n):
        """Проверка различных значений top_n"""
        df = pd.DataFrame({"amount": [100, 500, 250, 750, 150, 900, 300, 50, 600, 400]})

        result = get_top_transactions(df, top_n=top_n)
        assert len(result) == min(top_n, len(df))

        # Проверяем, что результат отсортирован по убыванию
        amounts = [item["amount"] for item in result]
        assert amounts == sorted(amounts, reverse=True)

    def test_top_transactions_default_top_5(self):
        """Проверка значения по умолчанию (топ-5)"""
        df = pd.DataFrame(
            {"amount": [100, 200, 300, 400, 500, 600, 700], "date": pd.date_range("2024-01-01", periods=7)}
        )

        result = get_top_transactions(df)
        assert len(result) == 5
        assert result[0]["amount"] == 700
        assert result[4]["amount"] == 300

    def test_top_transactions_with_duplicates(self):
        """Транзакции с одинаковыми суммами"""
        df = pd.DataFrame({"amount": [100, 200, 200, 300, 100], "description": ["A", "B", "C", "D", "E"]})

        result = get_top_transactions(df, top_n=3)
        assert len(result) == 3
        assert result[0]["amount"] == 300
