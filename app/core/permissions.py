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

    vehicle_assignment_create = "vehicle_assignment:create"
    vehicle_assignment_read = "vehicle_assignment:read"
    vehicle_assignment_update = "vehicle_assignment:update"
    vehicle_assignment_delete = "vehicle_assignment:delete"

    workshop_create = "workshop:create"
    workshop_read = "workshop:read"
    workshop_update = "workshop:update"
    workshop_delete = "workshop:delete"

    maintenance_work_order_create = "maintenance_work_order:create"
    maintenance_work_order_read = "maintenance_work_order:read"
    maintenance_work_order_update = "maintenance_work_order:update"
    maintenance_work_order_delete = "maintenance_work_order:delete"
    maintenance_work_order_schedule = "maintenance_work_order:schedule"
    maintenance_work_order_start = "maintenance_work_order:start"
    maintenance_work_order_complete = "maintenance_work_order:complete"
    maintenance_work_order_close = "maintenance_work_order:close"
    maintenance_work_order_cancel = "maintenance_work_order:cancel"

    activity_read = "activity:read"

    permission_grant = "permission:grant"
    permission_revoke = "permission:revoke"
