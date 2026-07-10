from .base import AuthenticationError


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid Token") -> None:
        super().__init__(message)


class ExpiredTokenError(AuthenticationError):
    def __init__(self, message: str = "Token Expired") -> None:
        super().__init__(message)
