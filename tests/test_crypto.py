import os
os.environ["PASTORAL_DEV"] = "1"
from server import crypto, audit
from recovery import shamir

def test_encrypt_roundtrip():
    key = crypto.load_key(None)
    blob = crypto.encrypt(b"hello", key)
    assert crypto.decrypt(blob, key) == b"hello"

def test_audit_chain_verifies():
    chain = []
    prev = ""
    for i in range(3):
        e = audit.append(prev, "care_x", "store", str(i))
        chain.append(e); prev = e["hash"]
    assert audit.verify(chain)
    chain[1]["actor"] = "tampered"
    assert not audit.verify(chain)

def test_shamir_2of3():
    secret = b"\x10" * 32
    shares = shamir.split(secret, 2, 3)
    assert shamir.combine(shares[:2]) == secret
    assert shamir.combine([shares[0], shares[2]]) == secret
    assert shamir.combine([shares[1], shares[2]]) == secret
