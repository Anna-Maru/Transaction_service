#  Transaction Service

**Transaction Service** — учебный курсовой проект № 1, предназначенный для обработки и анализа пользовательских транзакций.  
Проект реализует функции работы с данными, статистикой, валютными курсами и визуализацией через интерфейс представлений.

---

##  Структура проекта

```
Transaction_service/
├── src/ # Основной код приложения
│ ├── init.py
│ ├── utils.py # Вспомогательные функции (работа с датами, API, данными)
│ ├── views.py # Логика представлений и формирования JSON-ответов
│ ├── reports.py # Генерация отчетов
│ ├── services.py # Дополнительные бизнес-функции
│ └── main.py # Точка входа приложения
│
├── tests/ # Тесты для всех модулей
│ ├── init.py
│ ├── test_utils.py
│ ├── test_views.py
│ ├── test_reports.py
│ └── test_services.py
│
├── data/
│
├── .env
├── .env_template
├── .flake8
├── pyproject.toml / poetry.lock
└── README.md
```
## Установка и настройка

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/username/Transaction_service.git
   cd Transaction_service
   
2. **Создайте виртуальное окружение**

    ```bash
    python -m venv .venv
    source .venv/bin/activate       # macOS / Linux
    .venv\Scripts\activate          # Windows

3. **Установите зависимости и переменные окружения**
4. **Тестирование**

Запуск всех тестов:
    ```bash
    pytest -v
    
Проверка покрытия тестами:

```bash
pytest --cov=src --cov-report=html
