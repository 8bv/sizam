from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.models.request import Request
from .external_api import Wiki2035Worker


def make_request(session: Session, worker: Wiki2035Worker):
    stmt = select(Request).where(Request.status != "completed")
    for row in session.scalars(stmt):
        worker.update_status()
