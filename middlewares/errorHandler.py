from __future__ import annotations

import logging

from fastapi import HTTPException
from fastapi.exception_handlers import http_exception_handler
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


_EXCEPTION_MAP: dict[type, tuple[str, int]] = {}


def registerError(code: str, status: int):
    def wrapper(cls: type):
        _EXCEPTION_MAP[cls] = (code, status)
        return cls
    return wrapper


def _mapException(exc: Exception) -> tuple[str, int, str]:
    for exc_type, (code, status) in _EXCEPTION_MAP.items():
        if isinstance(exc, exc_type):
            return code, status, str(exc)

    msg = str(exc) if str(exc) else "An unexpected error occurred"

    if isinstance(exc, ValueError):
        return "bad_request", 400, msg
    if isinstance(exc, FileNotFoundError):
        return "not_found", 404, msg
    if isinstance(exc, PermissionError):
        return "forbidden", 403, msg

    return "internal_error", 500, msg


async def exceptionHandler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    code, status, message = _mapException(exc)
    logger.warning(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
    )
