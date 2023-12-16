import os
import secrets
from typing import NoReturn, Annotated

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.api_key import APIKeyHeader
from starlette import status

SECURITY = HTTPBasic()
API_KEY_HEADER_MODEL = APIKeyHeader(name="X-Api-Key")


def get_api_key(
        api_key_header: str = Security(API_KEY_HEADER_MODEL)
) -> NoReturn:
    return api_key_header
    # if api_key_header != os.environ["X-API-KEY"]:
    #     raise HTTPException(
    #         status_code=401, detail="Couldn't validate API key."
    #     )


def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(SECURITY)]
):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"admin"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = os.environ["ADMIN_PASSWORD"].encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
