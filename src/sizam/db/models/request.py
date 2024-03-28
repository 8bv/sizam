from enum import Enum
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from .base import Base, intpk, num_12_6, WithTimestamp


class RequestStatus(Enum):
    PENDING = "pending"
    RETRYING = "retrying"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    COMPLETED = "completed"


class Endpoint(Base):
    __tablename__ = "endpoint"

    id: Mapped[intpk]
    value: Mapped[str] = mapped_column(unique=True)

    requests: Mapped[List["Request"]] = relationship(back_populates="endpoint")


class RequestFile(Base, WithTimestamp):
    __tablename__ = "request_file"

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"), primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"), primary_key=True)

    file: Mapped["File"] = relationship(back_populates="request_associations")
    request: Mapped["Request"] = relationship(back_populates="file_associations")


class Request(Base, WithTimestamp):
    __tablename__ = "request"

    id: Mapped[intpk]
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoint.id"))
    endpoint: Mapped["Endpoint"] = relationship(
        back_populates="requests", lazy="joined"
    )
    data: Mapped[str]
    status: Mapped[RequestStatus]

    files: Mapped[List["File"]] = relationship(
        back_populates="requests", secondary=RequestFile.__table__
    )
    file_associations: Mapped[List[RequestFile]] = relationship(
        back_populates="request", viewonly=True, lazy="selectin"
    )
    responses: Mapped[List["Response"]] = relationship(back_populates="request")


class File(Base, WithTimestamp):
    __tablename__ = "file"

    id: Mapped[intpk]
    name: Mapped[Optional[str]]
    purpose: Mapped[Optional[str]]
    content: Mapped[bytes]
    hash: Mapped[str]
    requests: Mapped[List["Request"]] = relationship(
        back_populates="files", secondary=RequestFile.__table__
    )
    request_associations: Mapped[List[RequestFile]] = relationship(
        back_populates="file", viewonly=True
    )


class Response(Base, WithTimestamp):
    __tablename__ = "response"

    id: Mapped[intpk]
    content: Mapped[str]
    status_code: Mapped[int]
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"))
    duration: Mapped[num_12_6]

    request: Mapped[Request] = relationship(back_populates="responses")
