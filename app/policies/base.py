from typing import Any, Callable

from sqlalchemy import Select

from app.core.exceptions import InsufficientPermissionError
from app.models.user import User


class Policy:
    """
    Base class for resource authorization policies.

    Subclasses should override only the methods relevant to the resource.

    Unimplemented operations raise ``NotImplementedError``.
    """

    @staticmethod
    def scope(query: Select[Any], current_user: User) -> Select[Any]:
        """Restrict a query to resources visible to the current user"""
        return query

    @staticmethod
    def can_create(current_user: User) -> bool:
        """Return whether the current user can create the resource."""
        raise NotImplementedError

    @staticmethod
    def can_read(current_user: User, resource: Any) -> bool:
        """Return whether the current user can read the resource."""
        raise NotImplementedError

    @staticmethod
    def can_update(current_user: User, resource: Any) -> bool:
        """Return whether the current user can update the resource."""
        raise NotImplementedError

    @staticmethod
    def can_delete(current_user: User, resource: Any) -> bool:
        """Return whether the current user can delete the resource."""
        raise NotImplementedError

    @classmethod
    def authorize(
        cls,
        check: Callable[..., bool],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Raise InsufficientPermissionError if an authorization check fails"""
        if not check(*args, **kwargs):
            raise InsufficientPermissionError
