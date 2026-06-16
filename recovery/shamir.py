"""Shamir Secret Sharing over GF(256) — 2-of-3 split for the device key.

Pure-Python, no external dependencies. Suitable for the documented recovery
flow: Shard A on pastor device, Shard B encrypted in cloud, Shard C with org.
Any two shards reconstruct the key.
"""
from __future__ import annotations
import secrets
from typing import List, Tuple

# Rijndael GF(2^8) tables
_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x ^= (_x << 1) & 0xFF
    if _EXP[_i] & 0x80:
        _x ^= 0x1B
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]

def _mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]

def _div(a: int, b: int) -> int:
    if a == 0:
        return 0
    if b == 0:
        raise ZeroDivisionError
    return _EXP[(_LOG[a] - _LOG[b]) % 255]

def _eval(coeffs: List[int], x: int) -> int:
    y = 0
    for c in reversed(coeffs):
        y = _mul(y, x) ^ c
    return y

def split(secret: bytes, threshold: int = 2, shares: int = 3) -> List[Tuple[int, bytes]]:
    if not 2 <= threshold <= shares <= 255:
        raise ValueError("bad params")
    out: List[Tuple[int, bytearray]] = [(i + 1, bytearray()) for i in range(shares)]
    for byte in secret:
        coeffs = [byte] + [secrets.randbelow(256) for _ in range(threshold - 1)]
        for i, (x, buf) in enumerate(out):
            buf.append(_eval(coeffs, x))
    return [(x, bytes(buf)) for x, buf in out]

def combine(shares: List[Tuple[int, bytes]]) -> bytes:
    if len(shares) < 2:
        raise ValueError("need >=2 shares")
    length = len(shares[0][1])
    if any(len(s[1]) != length for s in shares):
        raise ValueError("share length mismatch")
    out = bytearray()
    for pos in range(length):
        # Lagrange interpolation at x=0
        s = 0
        for j, (xj, yj) in enumerate(shares):
            num = 1
            den = 1
            for m, (xm, _) in enumerate(shares):
                if m == j:
                    continue
                num = _mul(num, xm)
                den = _mul(den, xj ^ xm)
            s ^= _mul(yj[pos], _div(num, den))
        out.append(s)
    return bytes(out)
