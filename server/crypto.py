"""Server-side content encryption.

Cloud only ever sees ciphertext. Key material is provided per-request by the
pastor's client (envelope encryption) OR derived from an org-level KMS key in
production. For the open-source scaffold we accept a base64 key via header and
fall back to a deterministic dev key when ENV indicates dev mode.

Algorithm: XChaCha20-Poly1305 (via PyNaCl) with random 24-byte nonce.
"""
from __future__ import annotations
import os
import base64
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random

KEY_BYTES = 32

def _dev_key() -> bytes:
    # Deterministic dev key so tests are reproducible. NEVER used in prod.
    return b"\x00" * KEY_BYTES

def load_key(b64: str | None) -> bytes:
    if b64:
        key = base64.b64decode(b64)
        if len(key) != KEY_BYTES:
            raise ValueError("content key must be 32 bytes")
        return key
    if os.environ.get("PASTORAL_DEV") == "1":
        return _dev_key()
    raise PermissionError("no content key supplied")

def encrypt(plaintext: bytes, key: bytes) -> bytes:
    box = SecretBox(key)
    nonce = nacl_random(SecretBox.NONCE_SIZE)
    return nonce + box.encrypt(plaintext, nonce).ciphertext

def decrypt(blob: bytes, key: bytes) -> bytes:
    box = SecretBox(key)
    nonce, ct = blob[: SecretBox.NONCE_SIZE], blob[SecretBox.NONCE_SIZE :]
    return box.decrypt(ct, nonce)
