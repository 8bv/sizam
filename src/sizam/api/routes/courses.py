import json
import logging
from datetime import date
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_platform_id, new_session, PlatformID, Stub
from ...parsers import get_data, InvalidHeader
from ...db.gateway import DBGateway
from ...db.models.request import File, Request, RequestStatus

router = APIRouter(prefix="/courses")
logger = logging.getLogger(__name__)


class UnitCourseStatus(str, Enum):
    REVIEW = "review"
    APPROVED = "approved"
    DECLINED = "declined"
    ACCEPTED = "accepted"
    TRANSFER = "transfer"
    FINISHED = "finished"
    EXPELLED = "expelled"
    UNKNOWN = "unknown"


class AcceptanceDifficultyLevel(str, Enum):
    elementary = "Начальный"
    intermediate = "Средний"
    advanced = "Продвинутый"


class ExpelledReasonChoice(str, Enum):
    reason_expelled_legitimate_user_application = "По желанию заявителя"
    reason_expelled_not_legitimate_absence = "Непосещаемость"


@router.post("/set_finished", status_code=201)
def set_finished_from_excel(
        excel_file: UploadFile,
        session: Annotated[DBGateway, Depends()],
        # Annotated[NewUser, Depends(Stub(NewUser))],
        platform_id: Annotated[PlatformID, Depends(Stub(PlatformID))]
        # ,  = Depends(get_platform_id)
):
    """Метод для завершения модуля"""
    try:
        data = get_data(excel_file.file)
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )
    session.add_all([
        Request(
            data=json.dumps({
                "unti_id": row.unit_id,
                "course_id": row.course_id,
                "platform_id": platform_id,
                "status": UnitCourseStatus.FINISHED.value
            }),
            status=RequestStatus.PENDING
        )
        for row in data
    ])
    return {"message": f"Будет послано запросов: {len(data)} на завершение модуля."}


@router.post("/set_approved", status_code=201)
def set_approved_from_excel(
        excel_file: UploadFile,
        flow_id: int,
        enter_exam_date: date,
        platform_id: Annotated[PlatformID, Depends(Stub(PlatformID))],
        session: Annotated[DBGateway, Depends()],
):
    """Метод для одобрения заявки"""
    try:
        data = get_data(excel_file.file)
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )
    session.add_all([
        Request(
            data=json.dumps({
                "unti_id": row.unit_id,
                "course_id": row.course_id,
                "platform_id": platform_id,
                "status": UnitCourseStatus.APPROVED.value,
                "flow": flow_id,
                "enter_exam_date": f"{enter_exam_date:%Y-%m-%d}",
            }),
            status=RequestStatus.PENDING
        )
        for row in data
    ])
    return {"message": f"Будет послано запросов: {len(data)} на одобрение."}


@router.post("/set_accepted", status_code=201)
def set_accepted_from_excel(
        excel_file: UploadFile,
        accept_date: date,
        admission_order_date: date,
        admission_order_number: str,
        difficulty_level: AcceptanceDifficultyLevel,
        platform_id: Annotated[PlatformID, Depends(Stub(PlatformID))],
        session: Annotated[DBGateway, Depends()],
):
    """Метод для зачисления"""
    try:
        data = get_data(excel_file.file)
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )
    session.add_all([
        Request(
            data=json.dumps({
                "unti_id": row.unit_id,
                "course_id": row.course_id,
                "platform_id": platform_id,
                "status": UnitCourseStatus.ACCEPTED.value,
                "admission_order_date": admission_order_date,
                "accept_date": f"{accept_date:%Y-%m-%d}",
                "admission_order_number": admission_order_number,
                "difficulty_level": difficulty_level.name
            }),
            status=RequestStatus.PENDING
        )
        for row in data
    ])
    return {"message": f"Будет послано запросов: {len(data)} на зачисление."}


@router.post("/set_expelled")
def set_expelled_from_excel(
        excel_file: UploadFile,
        reason_choice: ExpelledReasonChoice,
        reason_file: UploadFile,
        reason_file_ds: UploadFile,
        platform_id: Annotated[PlatformID, Depends(Stub(PlatformID))],
        session: Annotated[DBGateway, Depends()],
):
    """Метод для отчисления"""
    try:
        data = get_data(excel_file.file)
    except InvalidHeader as ex:
        raise HTTPException(
            status_code=422, detail=ex.args[0]
        )

    reason_file = File(
        name=reason_file.filename,
        content=reason_file.file,
        purpose="reason_file"
    )
    reason_file_ds = File(
        name=reason_file_ds.filename,
        content=reason_file_ds.file,
        purpose="reason_file_ds"
    )
    session.add_all([reason_file, reason_file_ds])

    session.add_all([
        Request(
            data=json.dumps({
                "unti_id": row.unit_id,
                "course_id": row.course_id,
                "platform_id": platform_id,
                "status": UnitCourseStatus.EXPELLED.value,
                "reason_choice": reason_choice.name,
            }),
            status=RequestStatus.PENDING,
            files=[reason_file, reason_file_ds]
        )
        for row in data
    ])
    return {"message": f"Будет послано запросов: {len(data)} на отчисление."}
