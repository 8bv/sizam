import logging
from typing import List

from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, HTTPException
from fastapi.security.api_key import APIKey

from src.sizam.presentation.api.security import get_api_key
from src.sizam.application.parsers import get_data, InvalidHeader
from src.sizam.application.external_api.wiki2035 import Worker, get_external_api_worker
from src.sizam.application.consts import UntiCourseStatus

router = APIRouter(prefix="/courses")
logger = logging.getLogger(__name__)


def _validate_excel(excel_file):
    if not excel_file.filename.endswith(("xlsx", "xls")):
        raise HTTPException(
            status_code=422, detail="File must be with valid excel extension."
        )


@router.post("/set_finished", status_code=201)
def set_finished_from_excel(
        excel_file: UploadFile,
        background_tasks: BackgroundTasks,
        worker: Worker = Depends(get_external_api_worker),
):
    """Завершил модуль"""
    _validate_excel(excel_file)
    try:
        data = get_data(excel_file.file, status=UntiCourseStatus.FINISHED)
        for row in data:
            background_tasks.add_task(worker.update_status, row)
        return {"message": f"Будет послано запросов: {len(data)} на завершение модуля."}
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )


@router.post("/set_approved", status_code=201)
def set_approved_from_excel(
        excel_file: UploadFile,
        background_tasks: BackgroundTasks,
        worker: Worker = Depends(get_external_api_worker),
):
    _validate_excel(excel_file)
    try:
        for row in get_data(excel_file.file, status=UntiCourseStatus.APPROVED):
            background_tasks.add_task(worker.update_status, row)
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )


@router.post("/set_accepted", status_code=201)
def set_accepted_from_excel(
        excel_file: UploadFile,
        background_tasks: BackgroundTasks,
        worker: Worker = Depends(get_external_api_worker),
):
    """Зачислен"""
    _validate_excel(excel_file)
    try:
        data = get_data(excel_file.file, status=UntiCourseStatus.ACCEPTED)
        for row in data:
            background_tasks.add_task(worker.update_status, row)
        return {"message": f"Будет послано запросов: {len(data)} на зачисление."}
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )


@router.post("/set_expelled")
def set_expelled_from_excel(
        excel_file: UploadFile,
        reason_file: UploadFile,
        reason_file_ds: UploadFile,
        worker: Worker = Depends(get_external_api_worker),
):
    _validate_excel(excel_file)
    for row in get_data(excel_file, status=UntiCourseStatus.FINISHED):
        worker.update_status(row, reason_file_path=reason_file, reason_file_ds_path=reason_file_ds)


@router.get("/{course_id}/")
def get_course_data(
        course_id: int,
        worker: Worker = Depends(get_external_api_worker),
        api_key: APIKey = Depends(get_api_key),
) -> List[int]:
    worker.api_key = api_key
    status_code, message = worker.get_unti_ids_by_course(course_id)
    logger.info("%d", status_code)
    return message
