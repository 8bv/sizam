import logging
from fastapi import FastAPI

from ..presentation.api.routes import courses_router


def create_app():
    app = FastAPI()
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    app.include_router(courses_router)
    return app
