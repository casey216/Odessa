from datetime import datetime, time, timedelta

from app.crud.base import BaseCrud


class BaseService[CrudT: BaseCrud]:
    FILTER_FIELDS: set
    DATE_FIELDS: list[tuple[str, str, str]]
    crud: CrudT

    @classmethod
    def _build_post_filters(cls, params):
        filters = {"and": []}

        if search := getattr(params, "search", None):
            if len(search) >= 2:
                filters["and"].append(cls.crud._build_q_filters(search))

        for field in cls.FILTER_FIELDS:
            value = getattr(params, field, None)
            if value is not None:
                filters["and"].append({field: value})

        for from_field, to_field, column in cls.DATE_FIELDS:
            if value := getattr(params, from_field, None):
                filters["and"].append(
                    {
                        f"{column}__gte": datetime.combine(
                            value,
                            time.min,
                        )
                    }
                )

            if value := getattr(params, to_field, None):
                filters["and"].append(
                    {
                        f"{column}__lt": datetime.combine(
                            value + timedelta(days=1),
                            time.min,
                        )
                    }
                )

        if getattr(params, "include_deleted", False):
            filters["and"].append({"include_deleted": True})

        return filters
