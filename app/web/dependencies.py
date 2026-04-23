from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.adapters.base.registry import SourceAdapterRegistry
from app.persistence.db import get_db_session


registry = SourceAdapterRegistry()


def get_session() -> Session:
    return next(get_db_session())


def get_registry() -> SourceAdapterRegistry:
    return registry
