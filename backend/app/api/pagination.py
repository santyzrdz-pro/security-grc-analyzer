"""Pagination helper."""
from __future__ import annotations

import math
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.common import Page

T = TypeVar("T")


def paginate(
    db: Session, stmt: Select, page: int, page_size: int, mapper
) -> Page:
    page = max(1, page)
    page_size = max(1, min(200, page_size))

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(count_stmt) or 0

    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all()
    items = [mapper(row) for row in rows]
    pages = math.ceil(total / page_size) if total else 0
    return Page(items=items, total=total, page=page, page_size=page_size, pages=pages)
