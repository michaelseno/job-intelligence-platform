from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.persistence.schema_guard import should_validate_schema_on_startup, validate_database_schema_current
from app.web.routes import router


settings = get_settings()
scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    if should_validate_schema_on_startup(settings.database_url):
        validate_database_schema_current(settings.database_url)
    if settings.scheduler_enabled and not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Job Intelligence Platform MVP", lifespan=lifespan)
app_dir = Path(__file__).resolve().parent
static_dir = app_dir / "static"
if not static_dir.exists():
    static_dir = app_dir / "web" / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.include_router(router)
