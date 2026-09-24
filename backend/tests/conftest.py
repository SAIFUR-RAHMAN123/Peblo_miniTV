import os
os.environ["DATABASE_URL"] = "postgresql+psycopg2://peblo:peblo@localhost:5432/peblo_tv_test"
os.environ["STORAGE_LOCAL_ROOT"] = "/tmp/peblo_test_storage"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine, SessionLocal
from app.main import app

ADMIN_HEADERS = {"Authorization": "Bearer admin-dev-key"}
EDITOR_HEADERS = {"Authorization": "Bearer editor-dev-key"}


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()