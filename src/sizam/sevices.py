import json
import logging
from json import JSONDecodeError
from typing import Dict, Tuple

from httpx import Client, Response as HTTPResponse
from httpx._types import FileTypes # noqa
from sqlalchemy.orm import Session

from .db.models.request import File, Response, Request, RequestStatus
from .db.repo import get_uncompleted_requests


logger = logging.getLogger(__name__)


def _get_status_for_resp(resp: HTTPResponse):
    error_types = {
        4: RequestStatus.CLIENT_ERROR,
        5: RequestStatus.SERVER_ERROR,
    }

    try:
        content = resp.json()
    except JSONDecodeError:
        return error_types[resp.status_code // 100]

    if content.get("success") is not None:
        return RequestStatus.COMPLETED

    if content.get("status", "").startswith("Application already in status"):
        return RequestStatus.COMPLETED

    return RequestStatus.RETRYING


class RequestMakerService:
    def __init__(self, db_session: Session, http_client: Client):
        self._db_session = db_session
        self._http_client = http_client
        self._running = False

    def run(self):
        self._running = True
        self.proceed_uncompleted_requests()

    def stop(self):
        self._running = False

    @property
    def is_running(self):
        return self._running

    def _make_request(self, req: Request) -> Tuple[RequestStatus, Response]:
        if req.file_associations:
            files = self._get_files_for_request(req)
        else:
            files = {}

        response = self._http_client.post(
            url=req.endpoint.value,
            data=json.loads(req.data),
            files=files,
        )
        logger.debug(
            "Sent data %s, to url %s. Got status code: %d",
            req.data, req.endpoint.value, response.status_code
        )

        status = _get_status_for_resp(response)
        response_model = Response(
            content=response.text,
            status_code=response.status_code,
            request_id=req.id,
            duration=response.elapsed.total_seconds(),
        )

        return status, response_model

    def _get_files_for_request(self, req: Request) -> Dict[str, FileTypes]:
        files = {}
        for file_association in req.file_associations:
            file_id = file_association.file_id
            file = self._db_session.get(File, file_id)
            files[file.purpose] = file.name, file.content
        return files

    def proceed_uncompleted_requests(self):
        while self._running:
            uncompleted_requests = get_uncompleted_requests(self._db_session).all()
            if not uncompleted_requests:
                self._running = False

            for request in uncompleted_requests:
                logger.debug("Proceeding request %s", request)
                request_status, response = self._make_request(request)
                request.status = request_status

                self._db_session.add(response)
                self._db_session.commit()
