import os, tempfile, importlib

def test_vault_roundtrip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import sidecar.vault as v
    importlib.reload(v)
    cid = v.add_identity("Jane Doe", phone="+10000000000")
    out = v.resolve(cid)
    assert out["name"] == "Jane Doe"
