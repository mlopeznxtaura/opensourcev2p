# Zero-Trust Pastoral Platform — Open Source v2p

Second iteration of the zero-trust pastoral care platform. Builds on v1 by
adding: JWT auth, Argon2id password hashing, XChaCha20-Poly1305 transcript
encryption, hash-chained audit log, Shamir 2-of-3 recovery shards, WebAuthn-
style device binding stubs, and a separated sidecar identity vault with
explicit CareID issuance.

The cloud platform still NEVER stores plaintext identities.

## Layout

```
server/      FastAPI cloud platform (pseudonymous CareIDs only)
sidecar/     Local identity vault (CareID -> human, encrypted at rest)
recovery/    Shamir 2-of-3 split-key recovery
tests/       Smoke + crypto round-trip tests
docs/        Threat model, recovery design, security checklist
agents.jsonl Gaps + follow-ups for downstream agents
```

## Run

```bash
pip install -r requirements.txt
uvicorn server.main:app --reload         # cloud API
python sidecar/vault.py                  # local pastor vault
pytest -q                                # tests
```

## What changed vs v1

- `server/` — adds auth, audit chain, encrypted-at-rest transcripts, RLS-ready schema notes
- `sidecar/` — CareID issuance, XChaCha20-Poly1305 (falls back to AES-GCM), export/import
- `recovery/` — Shamir Secret Sharing 2-of-3 implementation
- `tests/` — crypto round-trip and audit-chain integrity checks
- `agents.jsonl` — explicit list of unresolved gaps (env, network, deploy)

See `docs/THREAT_MODEL.md` and `docs/RECOVERY.md`.
