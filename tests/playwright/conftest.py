import os

import httpx
import pytest

BASE_URL = os.environ.get("DEMO_APP_URL", "http://127.0.0.1:8001")


@pytest.fixture(autouse=True)
def reset_demo_app():
    httpx.post(f"{BASE_URL}/__reset")
    yield
