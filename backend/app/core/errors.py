from fastapi import Request
from fastapi.responses import JSONResponse


class PrismError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code, self.message, self.status_code = code, message, status_code


async def prism_error_handler(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, PrismError):
        return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
    return JSONResponse(status_code=500, content={"error": {"code": "internal_error", "message": "An unexpected error occurred."}})
