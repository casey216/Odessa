from .base import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class InsufficientPermissionError(AuthorizationError):
    pass


class PermissionNotFoundError(NotFoundError):
    pass


class DuplicatePermissionError(ConflictError):
    pass


class InvalidPermissionError(ValidationError):
    pass
