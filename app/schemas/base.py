from typing import Any

from pydantic import BaseModel, model_validator

from app.core.pagination import PaginationParams


class FormBaseModel(BaseModel):
    """
    Inherit from this model instead of pydantic.BaseModel
    for any schema receiving HTML form data.
    """

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: (None if isinstance(v, str) and v.strip() == "" else v)
                for k, v in data.items()
            }
        return data


class QueryParams[FilterT: BaseModel](BaseModel):
    pagination: PaginationParams
    filters: FilterT
