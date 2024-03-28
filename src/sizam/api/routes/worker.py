from enum import Enum

from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from ..deps import new_requests_worker, Stub
from ...db.repo import get_count_of_uncompleted_requests
from ...sevices import RequestMakerService

router = APIRouter(prefix="/requests_worker")


@router.post("/run", status_code=201)
def run_service(
        background_tasks: BackgroundTasks,
        service: RequestMakerService = Depends(new_requests_worker)
):
    if service.is_running:
        return {"message": "Запросы уже обрабатываются."}

    background_tasks.add_task(service.run)


@router.post("/stop")
def stop_service(
        service: RequestMakerService = Depends(new_requests_worker)
):
    if service.is_running:
        service.stop()

    return {"message": "Сервис остановлен."}


@router.get("/state")
def service_state(
        service: RequestMakerService = Depends(new_requests_worker)
):
    return {"message": "Запущен" if service.is_running else "Остановлен"}


@router.get("/uncompleted_requests_count")
def get_uncompleted_requests_count(
        session: Session = Depends(Stub(Session))
) -> int:
    return get_count_of_uncompleted_requests(session)
