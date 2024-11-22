from decimal import Decimal
from datetime import datetime
from typing import Annotated

from sqlalchemy import func, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry


num_12_6 = Annotated[Decimal, 12]
intpk = Annotated[int, mapped_column(primary_key=True)]
timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.now()),
]
timestamp_upd = Annotated[
    datetime,
    mapped_column(
        nullable=False, server_default=func.now(), server_onupdate=func.now()
    ),
]


class Base(DeclarativeBase):
    registry = registry(
        type_annotation_map={
            num_12_6: Numeric(12, 6),
        }
    )


class WithTimestamp:
    created_at: Mapped[timestamp]
    updated_at: Mapped[timestamp_upd]
