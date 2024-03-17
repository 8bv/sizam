import os
import logging
from fastapi import FastAPI

from .deps import init_dependencies
from .routes import courses_router
from .routes import requests_service_router


def _set_environ_if_not_exists(key: str) -> None:
    value = os.environ.get(key)
    if value is not None:
        return

    os.environ[key] = input(f"Provide value for {key}: ")


def create_app():
    for necessary_env in ("DB_URI", "BASE_URL", "COMPANY_NAME", "API_KEY"):
        _set_environ_if_not_exists(necessary_env)

    app = FastAPI()
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    app.include_router(courses_router)
    app.include_router(requests_service_router)
    init_dependencies(app)
    return app
