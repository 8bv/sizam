import os
import logging
import time
from typing import List, Tuple

from httpx import Client, ConnectTimeout, ReadTimeout, RemoteProtocolError

from ..schemas import UntiSetStatusDTO, UntiCourseStatus


logger = logging.getLogger(__name__)


def get_external_api_worker():
    client = Client()
    worker = Worker.from_envs(client)
    try:
        yield worker
    finally:
        client.close()


class Worker:
    def __init__(self, session: Client, platform_id: str):
        self._session = session
        self._platform_id = platform_id

    @property
    def api_key(self):
        return self._session.headers["Authorization"]

    @api_key.setter
    def api_key(self, value):
        self._session.headers["Authorization"] = value

    @classmethod
    def from_envs(cls, session: Client):
        session.base_url = os.environ["BASE_URL"]
        session.headers["Authorization"] = os.environ["API_KEY"]
        return cls(session, os.environ["COMPANY_NAME"])

    def update_status(self, unti: UntiSetStatusDTO, **status_extra):
        logger.debug("Setting %s for %s", unti.status, unti.unti_id)

        files = {}

        if unti.status is UntiCourseStatus.EXPELLED:
            self._session.headers["Content-Type"] = "multipart/form-data"
            files = {
                "reason_file": status_extra.pop("reason_file_path"),
                "reason_file_ds": status_extra.pop("reason_file_ds_path")
            }

        data = {
            "platform_id": self._platform_id,
            "course_id": unti.course_id,
            "unti_id": unti.unti_id,
            "status": unti.status.value,
            **status_extra
        }

        have_to_retry = True
        while have_to_retry:
            try:
                response = self._session.post(
                    "/api/v6/course/enroll/update/",
                    data=data,
                    files=files,
                )
            except (ReadTimeout, ConnectTimeout, RemoteProtocolError) as ex:
                logger.exception("timeout for response with data: %s", data, exc_info=ex)
            else:
                logger.debug(
                    "time elapsed: %s, data sent: %s, response body: %s",
                    response.elapsed, data, response.json()
                )
                have_to_retry = False
                if response.elapsed.seconds < 1:
                    time.sleep(1 - response.elapsed.seconds)

    def get_unti_ids_by_course(self, course_id: int) -> Tuple[int, List[int]]:
        result = []
        page = 1
        logger.info(self._session.headers)

        while True:
            response = self._session.get(
                "/api/v2/ticket_application/",
                params={"platform_id": self._platform_id, "course_id": course_id, "page": page}
            )
            if response.status_code != 200:
                return response.status_code, []

            data = response.json()
            result.extend(row["unti_id"] for row in data["results"])
            if data.get("next") is None:
                break

            page += 1

        return 200, result
