from .base import ValidationError


class PasswordError(ValidationError):
    def __init__(self, message: str):
        super().__init__(message)


class DateFilterError(ValidationError):
    def __init__(self, date_field: str) -> None:
        super().__init__(f"{date_field}_from must be before or equal to {date_field}_to")


class InvalidStatusTransitionError(ValidationError):
    def __init__(self, current_status: str, target_status: str) -> None:
        super().__init__(f"Cannot move work order from '{current_status}' to '{target_status}'")


class ImmutableStateError(ValidationError):
    def __init__(self, current_state: str, attempted_action: str, resource: str) -> None:
        super().__init__(f"Cannot {attempted_action} {resource} in '{current_state}' state.")
