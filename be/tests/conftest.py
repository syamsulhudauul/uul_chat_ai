import pytest
from cryptography.hazmat.primitives.asymmetric import ec

import app.auth as auth_module


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    """Stands in for jwt.PyJWKClient — always returns the same test public
    key rather than actually fetching a JWKS endpoint over the network.
    """

    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(self._public_key)


@pytest.fixture()
def jwks_private_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def _patch_jwks_client(monkeypatch, jwks_private_key):
    public_key = jwks_private_key.public_key()
    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda: _FakeJWKSClient(public_key))
