from typing import Optional

from sqlalchemy import func, select, ScalarResult
from sqlalchemy.orm import Session, selectinload

from .models.request import Endpoint, Request, RequestFile, RequestStatus
from .models.wiki2035 import (
    UnitWithCourse,
    UnitWithCourseFromFile,
    ExcelFile,
    BindUnitStatusFromExcelFile,
    UnitCourseStatus,
)


def get_or_create_endpoint(uri: str, session: Session) -> Endpoint:
    endpoint = session.scalar(select(Endpoint).where(Endpoint.value == uri))
    if endpoint is not None:
        return endpoint

    endpoint = Endpoint(value=uri)
    session.add(endpoint)
    return endpoint


def get_uncompleted_requests(session: Session) -> ScalarResult[Request]:
    return session.scalars(
        select(Request)
        .join(Endpoint)
        .options(selectinload(Request.file_associations).load_only(RequestFile.file_id))
        .where(
            Request.status.notin_(
                [RequestStatus.COMPLETED, RequestStatus.MAX_ATTEMPTS_EXCEED]
            )
        )
        .order_by(Request.updated_at)
        .limit(10)
    )


def get_top_10_requests(session: Session) -> ScalarResult[Request]:
    return session.scalars(
        select(Request)
        .join(Endpoint)
        .options(selectinload(Request.file_associations).load_only(RequestFile.file_id))
        .order_by(Request.updated_at)
        .limit(10)
    )


def get_count_of_uncompleted_requests(session: Session) -> int:
    return session.scalar(
        select(func.count(Request.id)).where(Request.status != RequestStatus.COMPLETED)
    )


def get_excel_file_by_hash(hash: str, session: Session) -> Optional[ExcelFile]:
    return session.scalar(select(ExcelFile).where(ExcelFile.hash == hash))


def get_units_with_course_by_file_id(
    file_id: int, session: Session
) -> ScalarResult[UnitWithCourse]:
    return session.scalars(
        select(UnitWithCourse)
        .select_from(UnitWithCourseFromFile)
        .join(UnitWithCourse)
        .where(UnitWithCourseFromFile.file_id == file_id)
    )


def get_bind_units_status_from_excel(
    file_id: int, session: Session
) -> ScalarResult[UnitCourseStatus]:
    return session.scalars(
        select(BindUnitStatusFromExcelFile.unit_status).where(
            BindUnitStatusFromExcelFile.file_id == file_id
        )
    )


def is_units_from_excel_has_status(
    file_id: int, status: UnitCourseStatus, session: Session
) -> bool:
    return (
        session.scalar(
            select(BindUnitStatusFromExcelFile.file_id).where(
                BindUnitStatusFromExcelFile.file_id == file_id,
                BindUnitStatusFromExcelFile.unit_status == status,
            )
        )
        is not None
    )
