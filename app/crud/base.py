from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select

from app.core.database import Base
from app.core.exceptions.base import NotFoundError, ValidationError


class FilterOp(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"


FilterGroup = dict[str, Any]


class BaseCrud[ModelT: Base]:
    """
    Generic CRUD service for SQLAlchemy models.

    Usage:
        class PermissionCrud(BaseCrud[Permission]):
            model = Permission
            equality_filters = ["name"]
    """

    MODEL: type[ModelT]
    ALLOWED_COLUMNS: dict[str, InstrumentedAttribute] = {}
    DEFAULT_SORT_COLUMN = "created_at"
    SEARCH_COLUMNS: tuple[str, ...]

    def _base_query(self) -> Select:
        return select(self.MODEL)

    def _exclude_soft_deleted(self, query: Select, *, include_deleted: bool) -> Select:
        deleted_at = getattr(self.MODEL, "deleted_at", None)
        if include_deleted or deleted_at is None:
            return query
        return query.where(deleted_at.is_(None))

    def _apply_filters(self, query: Select, filters) -> Select:
        if not filters:
            return query
        conditions = self._build_group(filters)
        return query.where(conditions) if conditions is not None else query

    def _apply_sort(self, query: Select, sort_by: str | None, order_by: str) -> Select:
        if sort_by is None:
            sort_by = self.DEFAULT_SORT_COLUMN

        column = self.ALLOWED_COLUMNS.get(sort_by)
        if column is None:
            raise ValidationError(
                f"Not valid column for '{sort_by}' "
                f"or default '{self.DEFAULT_SORT_COLUMN}'"
            )

        order_fn = desc if order_by == "desc" else asc
        return query.order_by(order_fn(column))

    async def create(self, db: AsyncSession, data: dict) -> ModelT:
        instance = self.MODEL(**data)
        db.add(instance)
        await db.flush()
        return instance

    async def get(self, db: AsyncSession, id: UUID) -> ModelT | None:
        return await db.get(self.MODEL, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> ModelT:
        instance = await self.get(db, id)
        if not instance:
            raise NotFoundError(self.MODEL.__name__, id)
        return instance

    def build_query(
        self,
        filters=None,
        sort_by: str = "created_at",
        order_by: str = "desc",
        include_deleted: bool = False,
    ) -> Select:
        query = self._base_query()
        query = self._exclude_soft_deleted(query, include_deleted=include_deleted)
        query = self._apply_filters(query, filters)
        query = self._apply_sort(query, sort_by, order_by)

        return query

    async def count(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = select(func.count()).select_from(self.MODEL)
        stmt = self._exclude_soft_deleted(stmt, include_deleted=include_deleted)
        stmt = self._apply_filters(stmt, filters)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        return await self.get(db, id) is not None

    async def update(self, db: AsyncSession, id: UUID, data: dict) -> ModelT:
        instance = await self.get_or_404(db, id)

        for key, value in data.items():
            if getattr(instance, key, None) != value:
                setattr(instance, key, value)

        await db.flush()
        return instance

    async def delete(self, db: AsyncSession, id: UUID) -> None:
        instance = await self.get_or_404(db, id)
        await db.delete(instance)

    async def soft_delete(self, db: AsyncSession, id: UUID) -> None:
        instance = await self.get_or_404(db, id)
        setattr(instance, "deleted_at", datetime.now(UTC))

    async def restore(self, db: AsyncSession, id: UUID) -> ModelT:
        instance = await self.get_or_404(db, id)
        if not hasattr(instance, "deleted_at"):
            raise NotImplementedError(
                f"{self.MODEL.__name__} does not support soft delete"
            )
        setattr(instance, "deleted_at", None)
        await db.flush()
        return instance

    @classmethod
    def _build_q_filters(cls, q: str) -> dict[str, list]:
        return {"or": [{col: q} for col in cls.SEARCH_COLUMNS]}

    def _build_group(self, group: FilterGroup):
        if not group:
            return None

        if "or" in group and len(group) == 1:
            sub = [self._build_group(g) for g in group["or"]]
            sub = [c for c in sub if c is not None]
            return or_(*sub) if sub else None

        if "and" in group and len(group) == 1:
            sub = [self._build_group(g) for g in group["and"]]
            sub = [c for c in sub if c is not None]
            return and_(*sub) if sub else None

        conditions = []
        for key, value in group.items():
            if value is None:
                continue
            field, op = key.rsplit("__", 1) if "__" in key else (key, FilterOp.EQ.value)

            column = self.ALLOWED_COLUMNS.get(field)
            if column is None:
                raise ValidationError(f"Invalid filter field: {field}")

            conditions.append(self._build_condition(column, op, value))

        return and_(*conditions) if conditions else None

    @staticmethod
    def _build_condition(column: InstrumentedAttribute, op: str, value: Any):
        match op:
            case FilterOp.EQ.value:
                return column == value
            case FilterOp.NE.value:
                return column != value
            case FilterOp.GT.value:
                return column > value
            case FilterOp.GTE.value:
                return column >= value
            case FilterOp.LT.value:
                return column < value
            case FilterOp.LTE.value:
                return column <= value
            case FilterOp.IN.value:
                return column.in_(
                    value if isinstance(value, (list, tuple, set)) else [value]
                )
            case FilterOp.NOT_IN.value:
                return column.not_in(
                    value if isinstance(value, (list, tuple, set)) else [value]
                )
            case FilterOp.LIKE.value:
                return column.like(f"%{value}%")
            case FilterOp.ILIKE.value:
                return column.ilike(f"%{value}%")
            case FilterOp.IS_NULL.value:
                return column.is_(None) if value else column.is_not(None)
            case _:
                raise ValidationError(f"Unsupported filter operator: {op}")
