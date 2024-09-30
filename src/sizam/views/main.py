import hashlib
import json
import logging
from datetime import date
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Iterable, NamedTuple, Optional, Callable, NewType

from fastapi import (
    APIRouter,
    FastAPI,
    Form,
    Request,
    Depends,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, sessionmaker

from sizam.db.models.request import RequestStatus, Request as RequestModel, File as FileModel
from sizam.db.models.wiki2035 import (
    Course,
    ExcelFile,
    UnitCourseStatus,
    AcceptanceDifficultyLevel, BindUnitStatusFromExcelFile,
)
from sizam.db.repo import (
    get_top_10_requests,
    get_or_create_endpoint,
    get_units_with_course_by_file_id,
    get_excel_file_by_hash,
    is_units_from_excel_has_status,
)
from sizam.parsers import get_units_with_course_from_excel, InvalidHeader

templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))
router = APIRouter()
logger = logging.getLogger(__name__)
PlatformId = NewType("PlatformId", str)


class Stub:
    def __init__(self, dependency: Callable, **kwargs):
        self._dependency = dependency
        self._kwargs = kwargs

    def __call__(self):
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(other, Stub):
            return (
                self._dependency == other._dependency and self._kwargs == other._kwargs
            )
        else:
            if not self._kwargs:
                return self._dependency == other
            return False

    def __hash__(self):
        if not self._kwargs:
            return hash(self._dependency)
        serial = (
            self._dependency,
            *self._kwargs.items(),
        )
        return hash(serial)


class ExpelledReasonChoice(str, Enum):
    reason_expelled_legitimate_user_application = "По желанию заявителя"
    reason_expelled_legitimate_blocked = "В связи с блоком на ЕПГУ"
    reason_expelled_legitimate_illness = (
        "Заболевание, амбулаторное, стационарное, санаторное лечение"
    )
    reason_expelled_legitimate_accomodation = "Изменение места жительства"
    reason_expelled_legitimate_family = "Особые семейные обстоятельства"
    reason_expelled_legitimate_war = "Особые условия нахождения Получателя услуги"
    reason_expelled_legitimate_army = "Невозможность завершения обучения"
    reason_expelled_legitimate_provider_error = "Ошибочно зачислен Провайдером"
    reason_expelled_legitimate_other = "Другое - уважительная"
    reason_expelled_not_legitimate_absence = "Непосещаемость"


@router.get("/start_process", response_class=HTMLResponse)
async def start_process(request: Request, session: Session = Depends(Stub(Session))):
    return templates.TemplateResponse(
        name="index.html",
        context={
            "urls": {
                "accepted": "Зачислить",
                "accepted_first_time": "Зачислить впервые",
                "expelled": "Отчислить",
                "finished": "Завершить",
            },
            "request": request,
        },
    )


@router.get("/upload_file", response_class=HTMLResponse)
async def upload_file(request: Request):
    return templates.TemplateResponse(
        name="file_upload.html",
        context={
            "request": request,
        },
    )


@router.post("/upload_file", response_class=HTMLResponse)
async def upload_file_form(
    request: Request,
    excel_file: UploadFile = File(),
    session: Session = Depends(Stub(Session)),
):
    file_hash = hashlib.file_digest(excel_file.file, "md5").hexdigest()
    existing_excel_file = get_excel_file_by_hash(file_hash, session)

    if existing_excel_file is not None:
        return templates.TemplateResponse(
            name="file_upload_button.html",
            context={"request": request, "last_file_id": existing_excel_file.id},
        )

    excel_file.file.seek(0)
    excel_file_obj = ExcelFile(
        hash=file_hash, name=excel_file.filename, content=excel_file.file.read()
    )
    try:
        data = get_units_with_course_from_excel(excel_file.file)
    except InvalidHeader as ex:
        raise HTTPException(status_code=422, detail=ex.args[0])

    for index, unit in enumerate(data):
        data[index] = session.merge(unit)

    excel_file_obj.units.extend(data)
    session.add(excel_file_obj)
    session.commit()
    return templates.TemplateResponse(
        name="file_upload_button.html",
        context={"request": request, "last_file_id": excel_file_obj.id},
    )


@router.get("/history", response_class=HTMLResponse)
async def history(request: Request, session: Session = Depends(Stub(Session))):
    history_reqs = get_top_10_requests(session).all()
    return templates.TemplateResponse(
        name="history.html",
        context={
            "request": request,
            "history": history_reqs,
        },
    )


@router.get("/", response_class=RedirectResponse)
def home():
    return RedirectResponse(url="/upload_file")


class FormFieldParams(NamedTuple):
    title: str
    type: str
    name: str
    description: Optional[str] = None
    choices: Optional[Enum] = None


@router.get("/get_file_form", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse(
        name="file_form.html",
        context={
            "request": request,
            "fields": [
                FormFieldParams(
                    title="Загрузка файла с унтиками",
                    type="file",
                    name="excel_file",
                    description="Файл формата xlsx",
                )
            ],
            "button_description": "Загрузить",
        },
    )


@router.get("/methods", response_class=HTMLResponse)
async def methods_dispatcher(method: str, request: Request):
    context = {
        "action": f"set_{method}",
        "button_description": "Запустить",
        "request": request,
    }

    if method == "accepted":
        context["fields"] = []
    elif method == "accepted_first_time":
        context["fields"] = [
            FormFieldParams(title="Дата зачисления", type="date", name="accept_date"),
            FormFieldParams(
                title="Дата приказа", type="date", name="admission_order_date"
            ),
            FormFieldParams(
                title="Номер приказа", type="text", name="admission_order_number"
            ),
        ]
    elif method == "finished":
        context["fields"] = []
    elif method == "expelled":
        context["fields"] = [
            FormFieldParams(
                title="Загрузка файла с приказом",
                type="file",
                name="reason_file",
                description="Приказ в формате pdf",
            ),
            FormFieldParams(
                title="Загрузка файла цифровой подписи",
                type="file",
                name="reason_file_ds",
                description="Цифвровая подпись формата sig",
            ),
            FormFieldParams(
                title="Причина отчисления",
                type="choice",
                name="reason_choice",
                choices=ExpelledReasonChoice,
            ),
        ]
    return templates.TemplateResponse(name="methods_form.html", context=context)


@router.post("/set_finished")
def set_finished_from_excel(
    file_id: int = Form(),
    session: Session = Depends(Stub(Session)),
    platform_id: PlatformId = Depends(Stub(PlatformId)),
):
    """Метод для завершения модуля"""
    status = UnitCourseStatus.FINISHED
    already_has_status = is_units_from_excel_has_status(
        file_id, status, session
    )
    if already_has_status:
        return RedirectResponse("/upload_file", 303)

    session.add(BindUnitStatusFromExcelFile(
        file_id=file_id, unit_status=status,
    ))
    endpoint = get_or_create_endpoint("/api/v6/course/enroll/update/", session)
    target_units = get_units_with_course_by_file_id(file_id, session)

    session.add_all(
        [
            RequestModel(
                data=json.dumps(
                    {
                        "unti_id": row.unit_id,
                        "course_id": row.course_id,
                        "platform_id": platform_id,
                        "status": status.value,
                    }
                ),
                status=RequestStatus.PENDING,
                endpoint=endpoint,
            )
            for row in target_units
        ]
    )
    session.commit()

    return RedirectResponse("/start_process", 303)


@router.post("/set_approved")
def set_approved_from_excel(
    file_id: int = Form(),
    flow_id: int = Form(),
    enter_exam_date: date = Form(),
    session: Session = Depends(Stub(Session)),
    platform_id: PlatformId = Depends(Stub(PlatformId)),
):
    """Метод для одобрения заявки"""
    status = UnitCourseStatus.APPROVED
    already_has_status = is_units_from_excel_has_status(
        file_id, status, session
    )
    if already_has_status:
        return
    endpoint = get_or_create_endpoint("/api/v6/course/enroll/update/", session)
    target_units = get_units_with_course_by_file_id(file_id, session)

    session.add_all(
        [
            RequestModel(
                data=json.dumps(
                    {
                        "unti_id": row.unit_id,
                        "course_id": row.course_id,
                        "platform_id": platform_id,
                        "status": status.value,
                        "flow": flow_id,
                        "enter_exam_date": f"{enter_exam_date:%Y-%m-%d}",
                    }
                ),
                status=RequestStatus.PENDING,
                endpoint=endpoint,
            )
            for row in target_units
        ]
    )
    session.commit()

    return RedirectResponse("/start_process", 303)


@router.post("/set_accepted")
def set_accepted_from_excel(
    file_id: int = Form(),
    session: Session = Depends(Stub(Session)),
    platform_id: PlatformId = Depends(Stub(PlatformId)),
):
    """Метод для зачисления"""
    status = UnitCourseStatus.ACCEPTED
    already_has_status = is_units_from_excel_has_status(
        file_id, status, session
    )
    if already_has_status:
        return
    endpoint = get_or_create_endpoint("/api/v6/course/enroll/update/", session)
    target_units = get_units_with_course_by_file_id(file_id, session)

    session.add_all(
        [
            RequestModel(
                data=json.dumps(
                    {
                        "unti_id": row.unit_id,
                        "course_id": row.course_id,
                        "platform_id": platform_id,
                        "status": status.value,
                    }
                ),
                status=RequestStatus.PENDING,
                endpoint=endpoint,
            )
            for row in target_units
        ]
    )
    session.commit()

    return RedirectResponse("/start_process", 303)


@router.post("/set_accepted_first_time")
def set_accepted_first_time_from_excel(
    file_id: int = Form(),
    accept_date: date = Form(),
    admission_order_date: date = Form(),
    admission_order_number: str = Form(),
    session: Session = Depends(Stub(Session)),
    platform_id: PlatformId = Depends(Stub(PlatformId)),
):
    """Метод для зачисления впервые"""
    status = UnitCourseStatus.ACCEPTED
    already_has_status = is_units_from_excel_has_status(
        file_id, status, session
    )
    if already_has_status:
        return
    endpoint = get_or_create_endpoint("/api/v6/course/enroll/update/", session)
    target_units = get_units_with_course_by_file_id(file_id, session)

    session.add_all(
        [
            RequestModel(
                data=json.dumps(
                    {
                        "unti_id": row.unit_id,
                        "course_id": row.course_id,
                        "platform_id": platform_id,
                        "status": status.value,
                        "admission_order_date": f"{admission_order_date:%Y-%m-%d}",
                        "accept_date": f"{accept_date:%Y-%m-%d}",
                        "admission_order_number": admission_order_number,
                        "difficulty_level": session.get(
                            Course, row.course_id
                        ).acceptance_level.name,
                    }
                ),
                status=RequestStatus.PENDING,
                endpoint=endpoint,
            )
            for row in target_units
        ]
    )
    session.commit()

    return RedirectResponse("/start_process", 303)


@router.post("/set_expelled")
def set_expelled_from_excel(
    file_id: int = Form(),
    reason_choice: ExpelledReasonChoice = Form(),
    reason_file: UploadFile = File(),
    reason_file_ds: UploadFile = File(),
    session: Session = Depends(Stub(Session)),
    platform_id: PlatformId = Depends(Stub(PlatformId)),
):
    """Метод для отчисления"""
    status = UnitCourseStatus.EXPELLED
    already_has_status = is_units_from_excel_has_status(
        file_id, status, session
    )
    if already_has_status:
        return
    endpoint = get_or_create_endpoint("/api/v6/course/enroll/update/", session)
    target_units = get_units_with_course_by_file_id(file_id, session)

    reason_file = FileModel(
        name=reason_file.filename,
        content=reason_file.file.read(),
        purpose="reason_file",
    )
    reason_file_ds = FileModel(
        name=reason_file_ds.filename,
        content=reason_file_ds.file.read(),
        purpose="reason_file_ds",
    )
    session.add_all([reason_file, reason_file_ds])

    session.add_all(
        [
            RequestModel(
                data=json.dumps(
                    {
                        "unti_id": row.unit_id,
                        "course_id": row.course_id,
                        "platform_id": platform_id,
                        "status": status.value,
                        "reason_choice": reason_choice.name,
                    }
                ),
                status=RequestStatus.PENDING,
                files=[reason_file, reason_file_ds],
                endpoint=endpoint,
            )
            for row in target_units
        ]
    )
    session.commit()

    return RedirectResponse("/start_process", 303)


@router.post("/add_course_info")
def add_course_info(
    id: int,
    acceptance_difficulty_level: AcceptanceDifficultyLevel,
    name: Optional[str] = None,
    session: Session = Depends(Stub(Session)),
) -> int:
    course = Course(
        id=id,
        name=name,
        acceptance_level=acceptance_difficulty_level,
    )
    course = session.merge(course)
    session.commit()

    return course.id


def new_session(session_maker: sessionmaker) -> Iterable[Session]:
    with session_maker() as session:
        yield session


def create_app(session_maker, platform_id):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[Session] = partial(new_session, session_maker)
    app.dependency_overrides[PlatformId] = lambda: platform_id
    return app
