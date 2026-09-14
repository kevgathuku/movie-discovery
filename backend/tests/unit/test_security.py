from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import settings
from app.security import passwords, tokens


def test_hash_roundtrip():
    hashed = passwords.hash_password("s3cure-pass")
    assert hashed != "s3cure-pass"
    assert passwords.verify_password("s3cure-pass", hashed) is True
    assert passwords.verify_password("wrong", hashed) is False


def test_verify_malformed_hash_returns_false():
    assert passwords.verify_password("x", "not-a-hash") is False


def test_mint_decode_roundtrip():
    token = tokens.mint_access_token(user_id=7, role="admin")
    payload = tokens.decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_decode_rejects_expired():
    token = tokens.mint_access_token(user_id=1, role="user", expires_minutes=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        tokens.decode_access_token(token)


def test_decode_rejects_wrong_algorithm():
    other = jwt.encode(
        {
            "sub": "1",
            "role": "user",
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS512",
    )
    with pytest.raises(jwt.InvalidTokenError):
        tokens.decode_access_token(other)


def test_decode_rejects_unsigned():
    unsigned = jwt.encode(
        {"sub": "1", "role": "user", "type": "access"},
        key="",
        algorithm="none",
    )
    with pytest.raises(jwt.InvalidTokenError):
        tokens.decode_access_token(unsigned)


def test_decode_rejects_wrong_type():
    payload = {
        "sub": "1",
        "role": "user",
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        tokens.decode_access_token(token)


def test_refresh_token_is_opaque_and_hashed():
    token, token_hash = tokens.new_refresh_token()
    assert len(token) >= 48
    assert token_hash != token
    assert token_hash == tokens.hash_token(token)
