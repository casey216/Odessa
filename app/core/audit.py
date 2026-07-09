import json

from sqlalchemy import event, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import Base
from app.models.activity import ActivityLog

EXCLUDED_MODELS: set[type[Base]] = {ActivityLog}

IGNORE_FIELDS = {"updated_at", "created_at", "deleted_at"}


def _serialize(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _get_filtered_changes(instance: Base):
    state = inspect(instance)

    changes = {}

    for attr in state.attrs:
        if attr.key in IGNORE_FIELDS:
            continue

        hist = attr.history
        if not hist.has_changes():
            continue

        changes[attr.key] = {
            "before": _serialize(hist.deleted[0]) if hist.deleted else None,
            "after": _serialize(hist.added[0]) if hist.added else None,
        }

    return changes


def _snapshot(instance: Base):
    return {
        col.key: _serialize(getattr(instance, col.key))
        for col in inspect(instance).mapper.column_attrs
    }


def _build_log(instance, action: str, ctx: RequestContext) -> ActivityLog:
    details = {}
    if action == "create":
        details = {"snapshot": _snapshot(instance)}
    if action == "update":
        details = {"changes": _get_filtered_changes(instance)}
    if action == "delete":
        details = {"deleted_values": _snapshot(instance)}

    return ActivityLog(
        user_id=ctx.current_user.id,
        action=action,
        entity_type=type(instance).__name__,
        entity_id=instance.id,
        details=details,
        ip_address=ctx.ip_address,
    )


def register_audit_listener(db: AsyncSession, ctx: RequestContext) -> None:
    seen = set()
    pending_creates = set()

    sync_session = db.sync_session

    @event.listens_for(sync_session, "before_flush")
    def before_flush(session, flush_context, instances):
        for instance in list(session.new):
            if type(instance) not in EXCLUDED_MODELS:
                pending_creates.add(instance)

        for instance in list(session.dirty):
            if type(instance) not in EXCLUDED_MODELS and id(instance) not in seen:
                seen.add(id(instance))
                session.add(_build_log(instance, "update", ctx))

        for instance in list(session.deleted):
            if type(instance) not in EXCLUDED_MODELS and id(instance) not in seen:
                seen.add(id(instance))
                session.add(_build_log(instance, "delete", ctx))

    @event.listens_for(sync_session, "after_flush_postexec")
    def after_flush_postexec(session, flush_context):
        for instance in pending_creates:
            if id(instance) not in seen:
                seen.add(id(instance))
                session.add(_build_log(instance, "create", ctx))

        pending_creates.clear()

    @event.listens_for(sync_session, "after_commit")
    def after_commit(session):
        seen.clear()

    @event.listens_for(sync_session, "after_rollback")
    def after_rollback(session):
        seen.clear()
        pending_creates.clear()
