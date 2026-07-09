import jwt
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey


def make_token(
    private_key: EllipticCurvePrivateKey,
    sub: str = "user-123",
    email: str | None = "recruiter@example.com",
    **overrides,
) -> str:
    payload = {"sub": sub, "aud": "authenticated", **overrides}
    if email is not None:
        payload["email"] = email
    return jwt.encode(payload, private_key, algorithm="ES256")
