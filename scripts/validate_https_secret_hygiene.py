#!/usr/bin/env python3
"""Validate HTTPS field-test secret hygiene.

The project may generate local self-signed cert/key files under certs/ for phone
camera testing. Private keys must stay local and untracked.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
required = ["certs/", "*.key", "*.pem"]
missing = [item for item in required if item not in gitignore]
assert not missing, "missing gitignore entries for local cert secrets: " + ", ".join(missing)
print("✅ HTTPS local cert secret-hygiene contract validated")
