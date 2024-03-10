from fastapi import APIRouter, Depends, BackgroundTasks

from ..deps import new_requests_worker
from ...sevices import RequestMakerService

router = APIRouter(prefix="/requests_worker")


@router.post("/process_requests", status_code=201)
def process_requests(
        background_tasks: BackgroundTasks,
        service: RequestMakerService = Depends(new_requests_worker)
):
    if service.is_running:
        return {"message": "Запросы уже обрабатываются."}

    background_tasks.add_task(service.proceed_uncompleted_requests)


@router.post("/stop_service")
def stop_service(
        service: RequestMakerService = Depends(new_requests_worker)
):
    if service.is_running:
        service.stop()

    return {"message": "Сервис остановлен."}


@router.get("/stop_service")
def stop_service(
        service: RequestMakerService = Depends(new_requests_worker)
):
    return {"message": "Запущен" if service.is_running else "Остановлен"}
