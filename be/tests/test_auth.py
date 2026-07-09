from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_helpers import make_token

client = TestClient(app)


def test_me_requires_bearer_token():
    response = client.get("/me")
    assert response.status_code == 401


def test_me_rejects_invalid_token():
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_rejects_token_signed_with_wrong_key(jwks_private_key):
    wrong_key = ec.generate_private_key(ec.SECP256R1())
    bad_token = make_token(wrong_key, sub="user-123")

    response = client.get("/me", headers={"Authorization": f"Bearer {bad_token}"})

    assert response.status_code == 401


def test_me_returns_user_id_and_email_for_valid_token(jwks_private_key):
    token = make_token(jwks_private_key, sub="user-123", email="recruiter@example.com")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123", "email": "recruiter@example.com"}
