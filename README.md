# City Summary

CLI-утилита «Сводка по городу»: получает погоду и курс выбранной валюты к рублю
из внешних API, применяет простые правила и печатает сводку в консоль.

## Внешние API

- Погода: [Open-Meteo](https://open-meteo.com/) — сначала геокодинг города, затем текущая погода по координатам. Ключ не нужен.
- Курсы: [Frankfurter](https://frankfurter.dev/) — `GET https://api.frankfurter.dev/v2/rate/{currency}/RUB`.

## Требования

- Python 3.12
- `requests` (см. `requirements.txt`)

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Запуск

```bash
python main.py --city Moscow                  # курс USD→RUB (по умолчанию)
python main.py --city Moscow --currency EUR   # курс EUR→RUB
python main.py --city Moscow --json           # сводка в JSON
python main.py --city Moscow -v               # логи с run_id в stderr
```

Пример вывода:

```text
Город: Moscow
Погода: -3.2°C, clear sky
Тёплая одежда: да
USD→RUB: 92.15
Дорогой курс: нет
```

## Коды выхода

| Код | Значение |
|---|---|
| 0 | успех |
| 2 | ошибка аргументов |
| 3 | город или код валюты не найден |
| 4 | внешний сервис недоступен после повторов (или вернул некорректный ответ) |

## Структура

```text
city_summary/
├── main.py                 # CLI: argparse, вывод, коды выхода, logging с run_id
├── clients/                # только общение с внешними API
│   ├── exceptions.py       # исключения приложения
│   ├── http.py             # общий GET: timeout 10 с, 3 повтора, Retry-After для 429
│   ├── weather.py          # get_weather(city) -> dict
│   └── rates.py            # get_rate(currency) -> float, кэш на 5 минут
├── processing/
│   ├── preprocessing.py    # правила: warm_clothes, expensive, описание по умолчанию
│   └── service.py          # build_city_summary(city, currency="USD") -> dict
└── tests/                  # unittest + unittest.mock, без сетевых запросов
```

## Правила предобработки

- `warm_clothes: true`, если температура < 0 °C;
- `expensive: true`, если курс > 100 ₽;
- пустое описание погоды заменяется на `no description`;
- температура округляется до 0.1, курс — до 0.01.

## Надёжность

- Каждый внешний запрос — только GET с `timeout=10`.
- До 3 повторов после первой попытки при `Timeout`, `ConnectionError`, 500/502/503/504 и 429
  (для 429 используется числовой `Retry-After`, иначе экспоненциальная пауза).
- Ответы проверяются: статус, JSON, наличие и тип обязательных полей. Неожиданный ответ
  превращается в понятную ошибку приложения.

## Дополнительно

- логирование с `run_id` (флаг `-v`);
- кэш курса на 5 минут;
- тесты клиентов через `unittest.mock`;
- аннотации типов;
- флаг `--json`.

## Тесты

```bash
python -m unittest discover -s tests -t .
```
