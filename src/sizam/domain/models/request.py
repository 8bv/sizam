from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from .base import Base, WithTimestamp


class Endpoint(Base):
    __table_name__ = "endpoint"

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str]

    requests: Mapped[List["Request"]] = relationship(back_populates="endpoint")


class Request(Base, WithTimestamp):
    __table_name__ = "request"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("endpoint.id"))
    endpoint: Mapped["Endpoint"] = relationship(back_populates="requests")
    data: Mapped[str]
    status: Mapped[str]

    requests: Mapped[List["RequestFile"]] = relationship(back_populates="file")


class RequestFile(Base, WithTimestamp):
    __table_name__ = "request_file"

    file_id: Mapped[int] = mapped_column(ForeignKey("file.id"), primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("request.id"), primary_key=True)
    file: Mapped["File"] = relationship(back_populates="requests")
    requests: Mapped["Request"] = relationship(back_populates="file")


class File(Base, WithTimestamp):
    __table_name__ = "file"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[bytes]
    requests: Mapped[List["RequestFile"]] = relationship(back_populates="file")
