import os
from functools import partial
from typing import Callable, Iterable, NewType

from fastapi import Depends, FastAPI
from httpx import Client
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..sevices import RequestMakerService

PlatformId = NewType("PlatformId", str)


class Stub:
    """
    This class is used to prevent fastapi from digging into
    real dependencies attributes detecting them as request data

    So instead of
    `interactor: Annotated[Interactor, Depends()]`
    Write
    `interactor: Annotated[Interactor, Depends(Stub(Interactor))]`

    And then you can declare how to create it:
    `app.dependency_overrides[Interactor] = some_real_factory`

    https://github.com/Tishka17/fastapi-template/blob/master/src/app/api/depends_stub.py
    """

    def __init__(self, dependency: Callable, **kwargs):
        self._dependency = dependency
        self._kwargs = kwargs

    def __call__(self):
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(other, Stub):
            return (
                    self._dependency == other._dependency
                    and self._kwargs == other._kwargs
            )
        else:
            if not self._kwargs:
                return self._dependency == other
            return False

    def __hash__(self):
        if not self._kwargs:
            return hash(self._dependency)
        serial = (
            self._dependency,
            *self._kwargs.items(),
        )
        return hash(serial)


def new_requests_worker(
        session: Session = Depends(Stub(Session))
):
    with Client(base_url=os.environ["BASE_URL"]) as http_client:
        http_client.headers["Authorization"] = os.environ["API_KEY"]
        yield RequestMakerService(session, http_client)


def create_session_maker():
    db_uri = os.environ["DB_URI"]

    engine = create_engine(
        db_uri,
        echo=True,
        # pool_size=15,
        # max_overflow=15,
        # connect_args={
        #     "connect_timeout": 5,
        # },
    )
    return sessionmaker(engine)


def new_session(session_maker: sessionmaker) -> Iterable[Session]:
    with session_maker() as session:
        yield session


def get_platform_id() -> PlatformId:
    return PlatformId(os.environ["COMPANY_NAME"])


def init_dependencies(app: FastAPI):
    session_maker = create_session_maker()

    app.dependency_overrides[Session] = partial(new_session, session_maker)
    app.dependency_overrides[RequestMakerService] = new_requests_worker
    app.dependency_overrides[PlatformId] = get_platform_id
