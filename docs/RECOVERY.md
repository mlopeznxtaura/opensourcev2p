# Recovery Design

Device key K (32 bytes) is split via Shamir 2-of-3:

- Shard A — pastor device (Secure Enclave / TPM in prod)
- Shard B — encrypted with org pubkey, stored in cloud
- Shard C — held by org admin (hardware token)

Any two reconstruct K. Developer alone cannot reach K.

See `recovery/shamir.py`.
