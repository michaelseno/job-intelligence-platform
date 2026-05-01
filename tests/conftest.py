from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.persistence.models import Base
from app.web.routes import get_session_dependency
from app.domain.transient_ingestion import transient_ingestion_registry


@pytest.fixture(autouse=True)
def clear_transient_ingestion_registry():
    transient_ingestion_registry.clear()
    yield
    transient_ingestion_registry.clear()


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_session():
        yield session

    app.dependency_overrides[get_session_dependency] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
