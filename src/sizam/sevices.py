import json
import logging
from typing import Dict

from httpx import Client
from httpx._types import FileTypes # noqa
from sqlalchemy.orm import Session

from .db.models.request import File, Response, Request, RequestStatus
from .db.repo import get_uncompleted_requests


logger = logging.getLogger(__name__)


class RequestMakerService:
    def __init__(self, db_session: Session, http_client: Client):
        self._db_session = db_session
        # TODO: вынести в отдельный менеджер который будет очищать кэш
        self._files_cache = {}
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

    def _make_request(self, req: Request) -> Response:
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

        response_model = Response(
            content=response.text,
            status_code=response.status_code,
            request_id=req.id,
            duration=response.elapsed.total_seconds(),
        )
        return response_model

    def _get_files_for_request(self, req: Request) -> Dict[str, FileTypes]:
        files = {}
        for file_association in req.file_associations:
            file_id = file_association.file_id
            file = self._files_cache.get(file_id)
            if file is None:
                file = self._db_session.get(File, file_id)
                self._files_cache[file_id] = file
            files[file.purpose] = file.name, file.content
        return files

    def proceed_uncompleted_requests(self):
        while self._running:
            uncompleted_requests = get_uncompleted_requests(self._db_session).all()
            if not uncompleted_requests:
                self._running = False

            for request in uncompleted_requests:
                logger.debug("Proceeding request %s", request)
                response = self._make_request(request)
                # TODO: добавить случаи в которых необходимы повторы
                if response.status_code in range(500, 504):
                    request.status = RequestStatus.RETRYING
                elif response.status_code in range(400, 404):
                    request.status = RequestStatus.CLIENT_ERROR
                else:
                    request.status = RequestStatus.COMPLETED

                self._db_session.add(response)
                self._db_session.commit()
