from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import get_settings
from app.core.errors import PrismError, prism_error_handler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="PRISM API", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
    app.add_exception_handler(PrismError, prism_error_handler)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, __: Exception):
        return await prism_error_handler(_, PrismError("internal_error", "An unexpected error occurred.", 500))

    app.include_router(router)
    return app


app = create_app()
