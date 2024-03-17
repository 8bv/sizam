from sqlalchemy import func, select, ScalarResult
from sqlalchemy.orm import Session, selectinload

from .models.request import Endpoint, Request, RequestFile, RequestStatus


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
