from .base import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class InsufficientPermissionError(AuthorizationError):
    def __init__(
        self, message: str = "You do not have sufficient permissions for this action."
    ) -> None:
        super().__init__(message)


class PermissionNotFoundError(NotFoundError):
    pass


class DuplicatePermissionError(ConflictError):
    pass


class InvalidPermissionError(ValidationError):
    pass
