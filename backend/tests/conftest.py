"""Test configuration: every run uses a throwaway data directory and makes no OpenAI/Pinecone calls."""

import atexit
import os
import shutil
import sys
import tempfile

import pytest

# Must be set before any application module reads core.config
_DATA = tempfile.mkdtemp(prefix="ada-tests-")
atexit.register(shutil.rmtree, _DATA, ignore_errors=True)
os.environ.update({
    "PLATFORM_DATA_DIR": os.path.join(_DATA, "platform"),
    "LEGAL_DATA_DIR": os.path.join(_DATA, "legal"),
    "ENGINEERING_DATA_DIR": os.path.join(_DATA, "engineering"),
    "OPENAI_API_KEY": "test-key",
    "PINECONE_API_KEY": "test-key",
    "PINECONE_ENVIRONMENT": "us-east-1",
    "FRONTEND_ORIGINS": "http://localhost:3001",
    "REVALIDATE_SECRET": "",           # no outbound revalidation calls in tests
    "LOGIN_MAX_ATTEMPTS": "5",
    "BACKUP_DIR": os.path.join(_DATA, "backups"),
    "BACKUP_INTERVAL_HOURS": "0",      # no background backup thread in tests
})
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from api import routes_analytics, routes_contact  # noqa: E402
from services.platform_store import get_platform_store  # noqa: E402
from services.security import hash_password  # noqa: E402

# The contact store has a fixed path; point it at the temporary directory too
routes_contact.DATA_DIR = os.path.join(_DATA, "contact")
routes_contact.DB_PATH = os.path.join(routes_contact.DATA_DIR, "messages.db")

ORIGIN = {"Origin": "http://localhost:3001"}
PASSWORD = "Correct-Horse-Battery-9"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    get_platform_store().clear_rate_limits()
    yield


@pytest.fixture
def store():
    return get_platform_store()


def make_user(email: str, role: str = "member", must_change: bool = False, password: str = PASSWORD):
    s = get_platform_store()
    existing = s.get_user_by_email(email)
    if existing:
        s.delete_user(existing["id"])
    return s.create_user(email, email.split("@")[0].title(), hash_password(password), role, must_change)


def login(email: str, password: str = PASSWORD) -> TestClient:
    client = TestClient(main.app)
    response = client.post("/auth/login", json={"email": email, "password": password}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    return client


@pytest.fixture
def anon():
    return TestClient(main.app)


@pytest.fixture
def admin_client(request):
    email = f"admin-{request.node.name[:40].lower()}@example.com"
    make_user(email, "admin")
    return login(email)


@pytest.fixture
def member_client(request):
    email = f"member-{request.node.name[:40].lower()}@example.com"
    make_user(email, "member")
    return login(email)
