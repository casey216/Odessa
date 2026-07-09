from dataclasses import dataclass

from app.models import User


@dataclass
class RequestContext:
    current_user: User
    ip_address: str | None = None
    user_agent: str | None = None
