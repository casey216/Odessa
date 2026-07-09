from typing import Any


class DomainError(Exception):
    """Base class for business-rule violations raised by the service layer."""


class NotFoundError(DomainError):
    def __init__(self, resource: str, resource_id: Any) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} {resource_id} not found")


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthenticationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
