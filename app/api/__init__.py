from fastapi import FastAPI

from .history import router as history_router


def register_routes(app: FastAPI) -> None:
    app.include_router(history_router)

