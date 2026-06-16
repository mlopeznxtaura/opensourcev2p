# Production Hardening Checklist

- [ ] TLS 1.3 termination in front of FastAPI
- [ ] Real JWT secret from KMS (see agents.jsonl `PASTORAL_JWT_SECRET`)
- [ ] PostgreSQL with RLS (apply docs/RLS.sql)
- [ ] WebAuthn passkey enrollment for pastors
- [ ] Argon2id parameters tuned to >=250ms on target hardware
- [ ] Signed encrypted backups (age + minisign)
- [ ] Audit-chain external anchor (e.g. periodic notarization)
- [ ] Firecracker / gVisor isolation for any AI worker
- [ ] Remote attestation gating sidecar key release
