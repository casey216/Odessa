from abc import ABC, abstractmethod


class Policy(ABC):
    """Base class for authorization policies."""

    @staticmethod
    @abstractmethod
    def can_create(*args, **kwargs) -> bool:
        """Return whether the current user can create the resource."""

    @staticmethod
    @abstractmethod
    def can_read(*args, **kwargs) -> bool:
        """Return whether the current user can read the resource."""

    @staticmethod
    @abstractmethod
    def can_update(*args, **kwargs) -> bool:
        """Return whether the current user can update the resource."""

    @staticmethod
    @abstractmethod
    def can_delete(*args, **kwargs) -> bool:
        """Return whether the current user can delete the resource."""
