from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.web.routes import router

settings = get_settings()
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if getattr(settings, "scheduler_enabled", False) and not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(router)
