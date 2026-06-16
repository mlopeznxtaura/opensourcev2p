"""Local pastor identity vault.

Stores CareID -> human identity, encrypted at rest with a device-bound key.
Never exposed to the cloud. CareID generation uses 128 bits of randomness.
"""
from __future__ import annotations
import os
import json
import secrets
import sqlite3
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

DB = "identity_vault.db"
KEY_FILE = "device.key"

def _ensure_key() -> bytes:
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, "wb") as f:
            f.write(secrets.token_bytes(32))
        os.chmod(KEY_FILE, 0o600)
    with open(KEY_FILE, "rb") as f:
        return f.read()

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.execute(
        """CREATE TABLE IF NOT EXISTS identities(
            care_id TEXT PRIMARY KEY,
            encrypted_blob BLOB NOT NULL,
            created_at INTEGER NOT NULL
        )"""
    )
    return c

KEY = _ensure_key()
_box = SecretBox(KEY)

def _enc(plaintext: bytes) -> bytes:
    nonce = nacl_random(SecretBox.NONCE_SIZE)
    return nonce + _box.encrypt(plaintext, nonce).ciphertext

def _dec(blob: bytes) -> bytes:
    nonce, ct = blob[: SecretBox.NONCE_SIZE], blob[SecretBox.NONCE_SIZE :]
    return _box.decrypt(ct, nonce)

def new_care_id() -> str:
    return "care_" + secrets.token_urlsafe(16)

def add_identity(real_name: str, phone: str | None = None, notes: str | None = None) -> str:
    import time
    care_id = new_care_id()
    payload = json.dumps({"name": real_name, "phone": phone, "notes": notes}).encode()
    c = _conn()
    c.execute(
        "INSERT INTO identities(care_id, encrypted_blob, created_at) VALUES (?,?,?)",
        (care_id, _enc(payload), int(time.time())),
    )
    c.commit()
    return care_id

def resolve(care_id: str) -> dict | None:
    c = _conn()
    row = c.execute(
        "SELECT encrypted_blob FROM identities WHERE care_id=?", (care_id,)
    ).fetchone()
    if not row:
        return None
    return json.loads(_dec(row[0]).decode())

def export_encrypted() -> bytes:
    """Dump full vault (still encrypted with device key) for backup."""
    c = _conn()
    rows = c.execute("SELECT care_id, encrypted_blob, created_at FROM identities").fetchall()
    import base64
    return json.dumps(
        [
            {"care_id": cid, "blob_b64": base64.b64encode(b).decode(), "created_at": ts}
            for cid, b, ts in rows
        ]
    ).encode()

if __name__ == "__main__":
    print("Local Identity Vault Online")
    print("Try: add_identity('Jane Doe')")
