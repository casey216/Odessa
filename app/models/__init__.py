from .activity import ActivityLog
from .manufacturer import Manufacturer
from .permission import Permission, UserPermission
from .tag import Tag, vehicle_tags
from .user import User, UserRole
from .vehicle import Vehicle
from .vehicle_assignment import VehicleAssignment
from .vehicle_model import VehicleModel

__all__ = [
    "ActivityLog",
    "Manufacturer",
    "Permission",
    "Tag",
    "UserPermission",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleAssignment",
    "VehicleModel",
    "vehicle_tags",
]
