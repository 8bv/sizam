from enum import Enum
from typing import Optional, List

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import intpk, Base, timestamp
from .request import File


class AcceptanceDifficultyLevel(str, Enum):
    intermediate = "Начальный"
    elementary = "Базовый"
    advanced = "Продвинутый"


class UnitCourseStatus(str, Enum):
    REVIEW = "review"
    APPROVED = "approved"
    DECLINED = "declined"
    ACCEPTED = "accepted"
    ACCEPTED_FIRST_TIME = "accepted"
    TRANSFER = "transfer"
    FINISHED = "finished"
    EXPELLED = "expelled"
    UNKNOWN = "unknown"


class ExcelFile(File):
    __tablename__ = "excel_file"

    id: Mapped[int] = mapped_column(ForeignKey(File.id), primary_key=True)
    hash: Mapped[str]

    units: Mapped[List["UnitWithCourse"]] = relationship(
        back_populates="file",
        secondary=lambda: UnitWithCourseFromFile.__table__,
    )
    unit_associations: Mapped[List["UnitWithCourseFromFile"]] = relationship(
        back_populates="file", viewonly=True, lazy="selectin"
    )
    units_status: Mapped[List["BindUnitStatusFromExcelFile"]] = relationship(
        back_populates="file"
    )

    __mapper_args__ = {"polymorphic_identity": "excel_file"}


class UnitWithCourse(Base):
    __tablename__ = "unit_course"

    unit_id: Mapped[intpk]
    course_id: Mapped[intpk]
    created_at: Mapped[timestamp]

    file: Mapped[List[ExcelFile]] = relationship(
        back_populates="units",
        secondary=lambda: UnitWithCourseFromFile.__table__,
    )
    file_associations: Mapped[List["UnitWithCourseFromFile"]] = relationship(
        back_populates="unit", viewonly=True, lazy="selectin"
    )


class Course(Base):
    __tablename__ = "course"

    id: Mapped[intpk]
    name: Mapped[Optional[str]]
    acceptance_level: Mapped[AcceptanceDifficultyLevel]


class UnitWithCourseFromFile(Base):
    __tablename__ = "units_from_excel"

    unit_id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey(ExcelFile.id), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            [unit_id, course_id], [UnitWithCourse.unit_id, UnitWithCourse.course_id]
        ),
    )

    unit: Mapped[UnitWithCourse] = relationship(back_populates="file_associations")
    file: Mapped[ExcelFile] = relationship(back_populates="unit_associations")


class BindUnitStatusFromExcelFile(Base):
    __tablename__ = "units_bind_status"

    file_id: Mapped[int] = mapped_column(ForeignKey(ExcelFile.id), primary_key=True)
    unit_status: Mapped[UnitCourseStatus] = mapped_column("method", primary_key=True)
    created_at: Mapped[timestamp]

    file: Mapped[ExcelFile] = relationship(back_populates="units_status")
