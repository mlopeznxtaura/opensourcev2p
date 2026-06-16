"""Cloud storage. Stores only ciphertext + pseudonymous CareIDs.

Schema is PostgreSQL-RLS-ready (see docs/RLS.sql) but uses SQLite locally so
the scaffold runs without external services.
"""
from __future__ import annotations
import sqlite3
import json
from hashlib import sha256
from . import audit

DB_PATH = "care.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS records(
    id INTEGER PRIMARY KEY,
    care_id TEXT NOT NULL,
    ciphertext BLOB NOT NULL,
    content_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_care ON records(care_id);

CREATE TABLE IF NOT EXISTS audit_log(
    id INTEGER PRIMARY KEY,
    prev TEXT NOT NULL,
    hash TEXT NOT NULL,
    ts INTEGER NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    ref TEXT
);

CREATE TABLE IF NOT EXISTS users(
    care_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    webauthn_credential TEXT
);
"""

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.executescript(_SCHEMA)
    return conn

def _last_hash(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else ""

def store_ciphertext(conn: sqlite3.Connection, care_id: str, ciphertext: bytes, ts: int) -> int:
    digest = sha256(ciphertext).hexdigest()
    cur = conn.execute(
        "INSERT INTO records(care_id, ciphertext, content_hash, created_at) VALUES (?,?,?,?)",
        (care_id, ciphertext, digest, ts),
    )
    entry = audit.append(_last_hash(conn), care_id, "store", str(cur.lastrowid))
    conn.execute(
        "INSERT INTO audit_log(prev, hash, ts, actor, action, ref) VALUES (?,?,?,?,?,?)",
        (entry["prev"], entry["hash"], entry["ts"], entry["actor"], entry["action"], entry["ref"]),
    )
    conn.commit()
    return cur.lastrowid

def fetch_ciphertext(conn: sqlite3.Connection, record_id: int, care_id: str) -> bytes | None:
    row = conn.execute(
        "SELECT ciphertext FROM records WHERE id=? AND care_id=?",
        (record_id, care_id),
    ).fetchone()
    return row[0] if row else None

def audit_chain(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT prev, hash, ts, actor, action, ref FROM audit_log ORDER BY id"
    ).fetchall()
    return [dict(zip(("prev","hash","ts","actor","action","ref"), r)) for r in rows]
