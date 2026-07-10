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

    activity_read = "activity:read"

    permission_grant = "permission:grant"
    permission_revoke = "permission:revoke"
