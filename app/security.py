from fastapi import Header, HTTPException

from .config import get_settings


def require_service_token(x_service_token: str = Header(...)) -> None:
    if x_service_token != get_settings().service_token:
        raise HTTPException(status_code=401, detail="Invalid service token")
