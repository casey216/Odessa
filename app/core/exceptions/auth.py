from .base import AuthenticationError


class InvalidCredentialsError(AuthenticationError):
    pass


class InvalidTokenError(AuthenticationError):
    pass


class ExpiredTokenError(AuthenticationError):
    pass
