from sqlalchemy import func, select, ScalarResult
from sqlalchemy.orm import Session, selectinload

from .models.request import Endpoint, Request, RequestFile, RequestStatus
from .models.wiki2035 import UnitWithCourse


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
        .where(Request.status != RequestStatus.COMPLETED)
        .order_by(Request.updated_at)
        .limit(10)
    )


def get_count_of_uncompleted_requests(session: Session) -> int:
    return session.scalar(
        select(func.count(Request.id))
        .where(Request.status != RequestStatus.COMPLETED)
    )


def get_unit_with_course_from_file(
        file_id: int,
        session: Session,
) -> ScalarResult[UnitWithCourse]:
    return session.scalars(
        select(UnitWithCourse)
        .where(UnitWithCourse.file_id == file_id)
    )
