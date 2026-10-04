"""Собственные исключения для бота-ассистента."""


class WrongResponseCodeError(Exception):
    """API вернул код ответа, отличный от 200."""


class ApiRequestError(Exception):
    """Сбой при выполнении запроса к API."""
