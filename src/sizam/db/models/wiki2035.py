from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from .base import intpk, Base, timestamp
from .request import File


class UnitWithCourse(Base):
    __tablename__ = "unit_course"

    unit_id: Mapped[intpk]
    course_id: Mapped[intpk]
    created_at: Mapped[timestamp]
    file_id: Mapped[Optional[int]] = mapped_column(ForeignKey(File.id), nullable=True)

    file: Mapped[Optional[File]] = relationship()
