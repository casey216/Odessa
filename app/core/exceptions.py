from uuid import UUID


class DomainError(Exception):
    """Base class for business-rule violations raised by the service layer."""


class NotFoundError(DomainError):
    def __init__(self, resource: str, resource_id: UUID) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} {resource_id} not found")


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class AuthorizationError(DomainError): ...


class PasswordError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message)


class DateFilterError(ValidationError):
    def __init__(self, date_field: str) -> None:
        super().__init__(
            f"{date_field}_from must be before or equal to {date_field}_to"
        )
