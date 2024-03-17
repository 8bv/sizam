from decimal import Decimal
from datetime import datetime
from typing import Annotated

from sqlalchemy import Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry


num_12_6 = Annotated[Decimal, 12]


class Base(DeclarativeBase):
    registry = registry(
        type_annotation_map={
            num_12_6: Numeric(12, 6),
        }
    )


class WithTimestamp:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
