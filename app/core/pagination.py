from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

from app.core import constants

SkipQuery = Annotated[
    int,
    Query(
        ge=constants.MIN_PAGINATION_SKIP,
        description="Number of records to skip",
    ),
]

LimitQuery = Annotated[
    int,
    Query(
        ge=constants.MIN_PAGINATION_LIMIT,
        le=constants.MAX_PAGINATION_LIMIT,
        description="Maximum number of records to return",
    ),
]


@dataclass(frozen=True)
class Pagination:
    skip: int = constants.DEFAULT_PAGINATION_SKIP
    limit: int = constants.DEFAULT_PAGINATION_LIMIT


def get_pagination(
    skip: SkipQuery = constants.DEFAULT_PAGINATION_SKIP,
    limit: LimitQuery = constants.DEFAULT_PAGINATION_LIMIT,
) -> Pagination:
    return Pagination(skip=skip, limit=limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
