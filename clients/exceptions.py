"""Исключения приложения, в которые переводятся ошибки внешних сервисов."""


class ClientError(Exception):
    """Базовая ошибка слоя clients."""


class NotFoundError(ClientError):
    """Запрошенный объект не найден во внешнем сервисе."""


class CityNotFoundError(NotFoundError):
    """Город не найден сервисом геокодинга."""


class CurrencyNotFoundError(NotFoundError):
    """Код валюты не поддерживается сервисом курсов."""


class ServiceUnavailableError(ClientError):
    """Внешний сервис недоступен даже после повторных попыток."""


class InvalidResponseError(ServiceUnavailableError):
    """Внешний сервис вернул ответ неожиданного формата."""
