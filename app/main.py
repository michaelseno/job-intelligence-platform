from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.web.routes import router


settings = get_settings()
scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if settings.scheduler_enabled and not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Job Intelligence Platform MVP", lifespan=lifespan)
app.include_router(router)
