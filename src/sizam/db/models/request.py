from enum import Enum
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from .base import Base, WithTimestamp


class RequestStatus(Enum):
    PENDING = "pending"
    RETRYING = "retrying"
    COMPLETED = "completed"


class Endpoint(Base):
    __tablename__ = "endpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(unique=True)

    requests: Mapped[List["Request"]] = relationship(back_populates="endpoint")


class Request(Base, WithTimestamp):
    __tablename__ = "request"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoint.id"))
    endpoint: Mapped["Endpoint"] = relationship(back_populates="requests")
    data: Mapped[str]
    status: Mapped[RequestStatus]

    files: Mapped[List["RequestFile"]] = relationship(back_populates="file")


class RequestFile(Base, WithTimestamp):
    __tablename__ = "request_file"

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"), primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"), primary_key=True)
    file: Mapped["File"] = relationship(back_populates="requests")
    requests: Mapped["Request"] = relationship(back_populates="file")


class File(Base, WithTimestamp):
    __tablename__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]
    purpose: Mapped[Optional[str]]
    content: Mapped[bytes]
    requests: Mapped[List["RequestFile"]] = relationship(back_populates="file")


class Response(Base, WithTimestamp):
    __tablename__ = "response"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
    status_code: Mapped[int]
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"))

    request: Mapped[Request] = relationship(back_populates="responses")
