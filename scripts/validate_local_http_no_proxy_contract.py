#!/usr/bin/env python3
"""Ensure local acceptance scripts bypass host HTTP proxies.

Some Hermes/runtime shells inject http_proxy. Requests to localhost must not go
through that proxy, otherwise local Docker health checks can return proxy 502
while the containers themselves are healthy.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "scripts" / "validate_main_flow.py",
    ROOT / "scripts" / "human_ui_traversal.py",
]

missing = []
for path in FILES:
    text = path.read_text(encoding="utf-8")
    if "LOCAL_HTTP.trust_env = False" not in text:
        missing.append(f"{path.relative_to(ROOT)} missing LOCAL_HTTP.trust_env = False")
    if "requests.get(" in text or "requests.request(" in text:
        if "LOCAL_HTTP.get(" not in text and "LOCAL_HTTP.request(" not in text:
            missing.append(f"{path.relative_to(ROOT)} still uses global requests without no-proxy session")

assert not missing, "\n".join(missing)
print("✅ local HTTP no-proxy contract validated")
