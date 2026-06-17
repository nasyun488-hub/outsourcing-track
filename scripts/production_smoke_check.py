#!/usr/bin/env python3
"""生产环境冒烟检查。"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:  # nosec - 运维脚本按显式URL检查
        body = resp.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body[:120]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    results = []
    try:
        health = get_json(f"{args.api_url.rstrip('/')}/health")
        results.append({"name": "backend health", "ok": health.get("status") == "ok", "data": health})
    except Exception as exc:  # noqa: BLE001
        results.append({"name": "backend health", "ok": False, "error": str(exc)})

    try:
        with urllib.request.urlopen(args.base_url, timeout=5) as resp:  # nosec
            results.append({"name": "frontend", "ok": 200 <= resp.status < 400, "status": resp.status})
    except Exception as exc:  # noqa: BLE001
        results.append({"name": "frontend", "ok": False, "error": str(exc)})

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    if not all(item["ok"] for item in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
