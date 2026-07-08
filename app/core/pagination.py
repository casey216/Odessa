from math import ceil
from typing import Annotated, Type

from fastapi import Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=100)] = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginationLinks(BaseModel):
    self: str
    prev: str | None = None
    next: str | None = None


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
    links: PaginationLinks


def build_link(request: Request, page: int) -> str:
    query_params = dict(request.query_params)
    query_params["page"] = str(page)

    return str(request.url.replace_query_params(**query_params))


async def paginate[T](
    request: Request,
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    schema: Type[T],
) -> PaginatedResponse[T]:
    count_query = select(func.count()).select_from(query.subquery())

    total = await db.scalar(count_query) or 0

    result = await db.execute(query.offset(params.offset).limit(params.page_size))

    items = result.scalars().all()

    pages = ceil(total / params.page_size) if total else 0

    links = PaginationLinks(
        self=build_link(request, params.page),
        prev=(build_link(request, params.page - 1) if params.page > 1 else None),
        next=(build_link(request, params.page + 1) if params.page < pages else None),
    )

    return PaginatedResponse[T](
        items=list(items),
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=pages,
        links=links,
    )
