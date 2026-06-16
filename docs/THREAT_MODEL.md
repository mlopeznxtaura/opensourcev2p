# Threat Model — v2p

## Assets
- Pastoral transcripts, notes, files
- CareID <-> human identity mapping (sidecar only)
- Device key (sidecar), org recovery shard, cloud recovery shard

## Adversaries
1. Cloud breach (full DB read)
2. Lost / stolen pastor device
3. Malicious developer with prod access
4. Compromised org admin

## Guarantees
| Adversary | Sees content | Sees identity |
|---|---|---|
| 1 cloud breach | ciphertext only | no |
| 2 lost device | no (key wiped on remote attest fail — TODO) | no |
| 3 dev access  | ciphertext + CareIDs | no |
| 4 org admin   | 1 shard, insufficient alone | no |

## Recovery
2-of-3 Shamir over the device key. See RECOVERY.md.

## Out of scope (see agents.jsonl)
- Network transport (TLS termination)
- Secret provisioning (JWT secret, KMS)
- Production deployment / Firecracker isolation
- Remote-attestation device binding
