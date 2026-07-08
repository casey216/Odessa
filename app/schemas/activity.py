from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    details: dict
    ip_address: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogFilter(BaseModel):
    search: str | None = None
    user_id: UUID | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: UUID | None = None
    min_date: datetime | None = None
    max_date: datetime | None = None
