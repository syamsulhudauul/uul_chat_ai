import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

TEST_SECRET = "test-secret"


@pytest.fixture(autouse=True)
def _set_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", TEST_SECRET)


def _make_token(sub: str = "user-123", email: str = "recruiter@example.com", **overrides):
    payload = {"sub": sub, "email": email, "aud": "authenticated", **overrides}
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def test_me_requires_bearer_token():
    response = client.get("/me")
    assert response.status_code == 401


def test_me_rejects_invalid_token():
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_rejects_token_signed_with_wrong_secret():
    bad_token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated"}, "wrong-secret", algorithm="HS256"
    )
    response = client.get("/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert response.status_code == 401


def test_me_returns_user_id_and_email_for_valid_token():
    token = _make_token(sub="user-123", email="recruiter@example.com")
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123", "email": "recruiter@example.com"}
