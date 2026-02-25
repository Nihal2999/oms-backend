from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = 1
    limit: int = 10


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

    @classmethod
    def create(cls, data: List[T], total: int, page: int, limit: int):
        return cls(
            data=data,
            total=total,
            page=page,
            limit=limit,
            total_pages=(total + limit - 1) // limit
        )