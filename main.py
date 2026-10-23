"""CLI «Сводка по городу»."""

import argparse
import json
import logging
import re
import sys
import uuid
from typing import Any

from clients.exceptions import (
    CityNotFoundError,
    CurrencyNotFoundError,
    ServiceUnavailableError,
)
from processing.service import build_city_summary

EXIT_OK = 0
EXIT_BAD_ARGS = 2  # argparse сам завершает программу с кодом 2
EXIT_NOT_FOUND = 3
EXIT_UNAVAILABLE = 4


class RunIdFilter(logging.Filter):
    """Добавляет run_id в каждую запись лога, чтобы связать строки одного запуска."""

    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self.run_id
        return True


def setup_logging(verbose: bool) -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.addFilter(RunIdFilter(uuid.uuid4().hex[:8]))
    handler.setFormatter(
        logging.Formatter("%(levelname)s [run_id=%(run_id)s] %(name)s: %(message)s")
    )
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING, handlers=[handler])


def currency_code(value: str) -> str:
    code = value.upper()
    if not re.fullmatch(r"[A-Z]{3}", code):
        raise argparse.ArgumentTypeError(f"ожидается ISO-код из трёх букв, получено {value!r}")
    return code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сводка по городу: погода и курс валюты к рублю")
    parser.add_argument("--city", required=True, help="название города, например Moscow")
    parser.add_argument(
        "--currency", type=currency_code, default="USD", help="ISO-код валюты (по умолчанию USD)"
    )
    parser.add_argument("--json", action="store_true", help="вывести сводку в формате JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="подробные логи в stderr")
    args = parser.parse_args(argv)
    if not args.city.strip():
        parser.error("--city не может быть пустым")
    return args


def yes_no(flag: bool) -> str:
    return "да" if flag else "нет"


def format_summary(summary: dict[str, Any]) -> str:
    weather = summary["weather"]
    rates = summary["rates"]
    return "\n".join(
        [
            f"Город: {summary['city']}",
            f"Погода: {weather['temp_c']}°C, {weather['description']}",
            f"Тёплая одежда: {yes_no(weather['warm_clothes'])}",
            f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}",
            f"Дорогой курс: {yes_no(rates['expensive'])}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        summary = build_city_summary(args.city, args.currency)
    except CityNotFoundError:
        print(f"Ошибка: город {args.city!r} не найден", file=sys.stderr)
        return EXIT_NOT_FOUND
    except CurrencyNotFoundError:
        print(f"Ошибка: код валюты {args.currency!r} не найден", file=sys.stderr)
        return EXIT_NOT_FOUND
    except ServiceUnavailableError as exc:
        print(f"Ошибка: внешний сервис недоступен ({exc})", file=sys.stderr)
        return EXIT_UNAVAILABLE

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_summary(summary))
    return EXIT_OK


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
