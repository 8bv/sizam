# import os
from functools import partial
from typing import Callable, Iterable, NewType, Union

from fastapi import Depends, FastAPI
from httpx import Client
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session, sessionmaker

from ..config import Config, Wiki2035Config
from ..db.gateway import DBGateway
from ..sevices import RequestMakerService

PlatformID = NewType("PlatformID", str)


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
        external_service_web_config: Wiki2035Config,
        session: Session = Depends(Stub(Session))
):
    with Client(
            base_url=external_service_web_config.base_url
    ) as http_client:
        http_client.headers["Authorization"] = external_service_web_config.token
        yield RequestMakerService(session, http_client)


def create_session_maker(db_uri: Union[str, URL]):
    engine = create_engine(
        db_uri,
        echo=True,
        # pool_size=15,
        # max_overflow=15,
        connect_args={
            "connect_timeout": 5,
        },
    )
    return sessionmaker(engine)


def new_session(session_maker: sessionmaker) -> Iterable[Session]:
    with session_maker() as session:
        yield session


def new_gateway(session: Session = Depends(Stub(Session))):
    yield DBGateway(session)

def get_platform_id(external_service_web_config: Wiki2035Config):
    return external_service_web_config.platform_id


def init_dependencies(app: FastAPI, config: Config):
    session_maker = create_session_maker(config.db.sqla_url)

    app.dependency_overrides[Session] = partial(new_session, session_maker)
    app.dependency_overrides[DBGateway] = new_gateway
    app.dependency_overrides[RequestMakerService] = partial(new_requests_worker, config.wiki2035)
    app.dependency_overrides[PlatformID] = partial(get_platform_id, config.wiki2035)
