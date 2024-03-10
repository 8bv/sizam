import os
import logging
from fastapi import FastAPI

from ..config import load_config
from .deps import init_dependencies
from .routes import courses_router
from .routes import requests_service_router


def create_app():
    config_path = os.environ["CFGPA"]
    conf = load_config(config_path)
    app = FastAPI()
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
    app.include_router(courses_router)
    app.include_router(requests_service_router)
    init_dependencies(app, conf)
    return app
