import pytest
from app.main import tmp_db, app
from fastapi.testclient import TestClient


# this is a temporary fix to test the in memory dict db.
@pytest.fixture(autouse=True)
def reset_db():
    tmp_db["url_to_code"].clear()
    tmp_db["code_to_url"].clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)
