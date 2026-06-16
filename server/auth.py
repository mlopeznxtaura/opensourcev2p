"""JWT + Argon2id password hashing.

NOTE: JWT secret + token lifetime are loaded from env. See agents.jsonl for
the env keys that must be provisioned before production use.
"""
from __future__ import annotations
import os
import time
from jose import jwt
from passlib.hash import argon2

ALGO = "HS256"
DEFAULT_TTL = 3600

def hash_password(pw: str) -> str:
    return argon2.using(type="ID", memory_cost=64 * 1024, time_cost=3, parallelism=2).hash(pw)

def verify_password(pw: str, h: str) -> bool:
    try:
        return argon2.verify(pw, h)
    except Exception:
        return False

def _secret() -> str:
    # Intentionally unresolved — see agents.jsonl. Tests inject a fixture.
    return os.environ.get("PASTORAL_JWT_SECRET", "dev-only-not-secret")

def issue(care_id: str, ttl: int = DEFAULT_TTL) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": care_id, "iat": now, "exp": now + ttl},
        _secret(),
        algorithm=ALGO,
    )

def verify_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[ALGO])
