from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate
from app.crud.activity import ActivityLogCrud
from app.schemas.activity import ActivityLogOut
from app.schemas.base import QueryParams


class ActivityService:
    crud = ActivityLogCrud()

    async def get_activity_list(
        self, request: Request, db: AsyncSession, params: QueryParams
    ) -> PaginatedResponse[ActivityLogOut]:
        query = self.crud.fetch_all(
            params.filters, params.sort.sort_by, params.sort.sort_order
        )

        return await paginate(request, db, query, params.pagination, ActivityLogOut)


activity_service = ActivityService()
