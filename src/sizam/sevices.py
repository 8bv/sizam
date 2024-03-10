from typing import Dict

from httpx import Client
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .db.models.request import Endpoint, Response, Request, RequestFile, File


class RequestMakerService:
    def __init__(self, db_session: Session, http_client: Client):
        self._db_session = db_session
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
        if req.files:
            files = self._get_files_for_request(req)
        else:
            files = None

        response = self._http_client.post(
            url=req.endpoint.value,
            data=req.data,
            files=files,
        )

        response_model = Response(
            content=response.content,
            status_code=response.status_code,
            request_id=req.id,
        )
        return response_model

    def _get_files_for_request(self, req: Request) -> Dict[str, bytes]:
        files = {}
        for file_id in req.files:
            file = self._files_cache.get(file_id)
            if file is None:
                stmt = select(File).where(File.id == file_id)
                file = self._db_session.scalar(stmt)
                self._files_cache[file_id] = file
            files[file.name] = file.content
        return files

    def proceed_uncompleted_requests(self):
        stmt = (
            select(Request)
            .join(Endpoint)
            .where(Request.status != "completed")
            .order_by(Request.updated_at)
            .limit(10)
        ).options(
            selectinload(Request.files)
            .load_only(RequestFile.file_id)
        )
        while self._running:
            for request in self._db_session.scalars(stmt).all():
                response = self._make_request(request)
                if response.status_code in range(500, 503):
                    request.status = "retrying"
                else:
                    request.status = "completed"

                self._db_session.add(response)
                self._db_session.commit()
