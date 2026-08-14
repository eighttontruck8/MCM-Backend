from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


PBKDF2_ITERATIONS = 600_000


class TokenError(ValueError):
    pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
    except (TypeError, ValueError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(
    *,
    secret: str,
    subject: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    store_id: str | None = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    token_id = str(uuid4())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "jti": token_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": "m-journey",
    }
    if store_id is not None:
        payload["store_id"] = store_id
    encoded_header = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}", token_id, expires_at


def decode_token(token: str, secret: str, expected_type: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        header = json.loads(_b64decode(encoded_header))
        payload = json.loads(_b64decode(encoded_payload))
        signature = _b64decode(encoded_signature)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise TokenError("잘못된 토큰 형식입니다.") from exc

    if header != {"alg": "HS256", "typ": "JWT"}:
        raise TokenError("지원하지 않는 토큰입니다.")
    expected_signature = hmac.new(
        secret.encode(), f"{encoded_header}.{encoded_payload}".encode(), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenError("토큰 서명이 올바르지 않습니다.")
    required = {"sub", "role", "type", "jti", "iat", "exp", "iss"}
    if not required.issubset(payload) or payload["iss"] != "m-journey":
        raise TokenError("토큰 정보가 올바르지 않습니다.")
    if payload["type"] != expected_type:
        raise TokenError("토큰 종류가 올바르지 않습니다.")
    if not isinstance(payload["exp"], int) or payload["exp"] <= int(datetime.now(timezone.utc).timestamp()):
        raise TokenError("토큰이 만료되었습니다.")
    return payload
