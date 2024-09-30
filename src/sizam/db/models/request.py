from enum import Enum
from typing import List, Optional

from sqlalchemy import ForeignKey, case
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property

from .base import Base, intpk, num_12_6, WithTimestamp, timestamp


class RequestStatus(Enum):
    PENDING = "pending"
    RETRYING = "retrying"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    COMPLETED = "completed"
    MAX_ATTEMPTS_EXCEED = "max_attempts_exceed"


class Endpoint(Base):
    __tablename__ = "endpoint"

    id: Mapped[intpk]
    value: Mapped[str] = mapped_column(unique=True)

    requests: Mapped[List["Request"]] = relationship(back_populates="endpoint")


class RequestFile(Base):
    __tablename__ = "request_file"

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"), primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"), primary_key=True)
    created_at: Mapped[timestamp]

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
    attempts: Mapped[int] = mapped_column(default=0)

    files: Mapped[List["File"]] = relationship(
        back_populates="requests", secondary=RequestFile.__table__
    )
    file_associations: Mapped[List[RequestFile]] = relationship(
        back_populates="request", viewonly=True, lazy="selectin"
    )
    responses: Mapped[List["Response"]] = relationship(back_populates="request")


class File(Base):
    __tablename__ = "file"

    id: Mapped[intpk]
    name: Mapped[Optional[str]]
    purpose: Mapped[Optional[str]] = mapped_column()
    content: Mapped[bytes]
    created_at = Mapped[timestamp]
    requests: Mapped[List["Request"]] = relationship(
        back_populates="files", secondary=RequestFile.__table__
    )
    request_associations: Mapped[List[RequestFile]] = relationship(
        back_populates="file", viewonly=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "regular_file",
        "polymorphic_on": case(
            (purpose == "excel_file", "excel_file"),
            else_="regular_file"
        ),
    }


class Response(Base):
    __tablename__ = "response"

    id: Mapped[intpk]
    content: Mapped[str]
    status_code: Mapped[int]
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"))
    duration: Mapped[num_12_6]
    created_at: Mapped[timestamp]

    request: Mapped[Request] = relationship(back_populates="responses")
