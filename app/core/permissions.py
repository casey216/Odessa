from enum import StrEnum


class PermissionCode(StrEnum):
    user_create = "user:create"
    user_read = "user:read"
    user_update = "user:update"
    user_delete = "user:delete"
    user_activate = "user:activate"
    user_deactivate = "user:deactivate"

    manufacturer_create = "manufacturer:create"
    manufacturer_read = "manufacturer:read"
    manufacturer_update = "manufacturer:update"
    manufacturer_delete = "manufacturer:delete"

    vehicle_model_create = "vehicle_model:create"
    vehicle_model_read = "vehicle_model:read"
    vehicle_model_update = "vehicle_model:update"
    vehicle_model_delete = "vehicle_model:delete"

    vehicle_create = "vehicle:create"
    vehicle_read = "vehicle:read"
    vehicle_update = "vehicle:update"
    vehicle_delete = "vehicle:delete"

    activity_read = "activity:read"

    permission_grant = "permission:grant"
    permission_revoke = "permission:revoke"
