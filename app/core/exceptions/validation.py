from .base import ValidationError


class PasswordError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message)


class DateFilterError(ValidationError):
    def __init__(self, date_field: str) -> None:
        super().__init__(
            f"{date_field}_from must be before or equal to {date_field}_to"
        )
