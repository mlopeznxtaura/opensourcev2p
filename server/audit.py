"""Hash-chained audit log.

Each entry stores: prev_hash, payload_hash, timestamp, actor_care_id, action.
Tampering with any past entry breaks the chain.
"""
from __future__ import annotations
import json
import time
from hashlib import sha256
from typing import Iterable

GENESIS = "0" * 64

def _hash(prev: str, payload: dict) -> str:
    blob = prev + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(blob.encode()).hexdigest()

def append(prev_hash: str, actor: str, action: str, ref: str | None = None) -> dict:
    payload = {
        "ts": int(time.time()),
        "actor": actor,
        "action": action,
        "ref": ref,
    }
    h = _hash(prev_hash or GENESIS, payload)
    return {"prev": prev_hash or GENESIS, "hash": h, **payload}

def verify(chain: Iterable[dict]) -> bool:
    prev = GENESIS
    for entry in chain:
        expect = _hash(prev, {k: entry[k] for k in ("ts", "actor", "action", "ref")})
        if entry["hash"] != expect or entry["prev"] != prev:
            return False
        prev = entry["hash"]
    return True
