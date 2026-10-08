from datetime import UTC, datetime, timedelta
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from os import urandom
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aquasentinel.config import get_settings

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    actual_salt = salt or urandom(16)
    digest = pbkdf2_hmac("sha256", password.encode(), actual_salt, 310_000)
    return f"pbkdf2_sha256$310000${actual_salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256" or int(iterations) < 310_000:
            return False
        actual = pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations)).hex()
    except (ValueError, TypeError):
        return False
    return compare_digest(actual, expected)


def create_access_token(subject: str, roles: list[str], regions: list[str]) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {"sub": subject, "roles": roles, "regions": regions, "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes), "iss": "aquasentinel", "aud": "aquasentinel-api"}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_access_token(token: str) -> dict:
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=["HS256"],
            audience="aquasentinel-api",
            issuer="aquasentinel",
            options={"require": ["sub", "exp", "iat", "roles", "regions"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "invalid or expired bearer token") from exc
    if not isinstance(claims.get("roles"), list) or not isinstance(claims.get("regions"), list):
        raise HTTPException(401, "invalid token scope")
    return claims


def current_actor(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict:
    if credentials is None:
        raise HTTPException(401, "bearer token required")
    return verify_access_token(credentials.credentials)


def authorize(actor: dict, region_id: str, roles: set[str]) -> None:
    if not set(actor["roles"]).intersection(roles):
        raise HTTPException(403, "role not permitted")
    if region_id not in actor["regions"] and "*" not in actor["regions"]:
        raise HTTPException(403, "region not permitted")


Actor = Annotated[dict, Depends(current_actor)]
