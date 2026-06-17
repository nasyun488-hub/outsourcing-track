#!/usr/bin/env python3
"""Validate P0 mobile camera scan field-readiness contract.

This is not a fake claim of real-phone acceptance. It checks that the codebase now
contains the minimum assets needed to execute true mobile camera validation:
- HTTPS nginx/docker profile for getUserMedia on phones
- QR sample generation script for real scan targets
- Scan page secure-context/operator guidance
- Field-test checklist/report template with DB/API cross-check steps
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required_files = {
    "HTTPS nginx config": ROOT / "frontend" / "nginx.https.conf",
    "HTTPS compose override": ROOT / "docker-compose.https.yml",
    "QR sample generator": ROOT / "scripts" / "generate_mobile_scan_qr_samples.mjs",
    "mobile field checklist": ROOT / "docs" / "acceptance" / "mobile-camera-field-test-checklist-2026-06-16.md",
}
missing_files = [name for name, path in required_files.items() if not path.exists()]
assert not missing_files, "Missing P0 mobile camera readiness files: " + ", ".join(missing_files)

scan_page = (ROOT / "frontend" / "src" / "views" / "ScanPage.vue").read_text(encoding="utf-8")
https_conf = (ROOT / "frontend" / "nginx.https.conf").read_text(encoding="utf-8")
compose_https = (ROOT / "docker-compose.https.yml").read_text(encoding="utf-8")
qr_script = (ROOT / "scripts" / "generate_mobile_scan_qr_samples.mjs").read_text(encoding="utf-8")
checklist = (ROOT / "docs" / "acceptance" / "mobile-camera-field-test-checklist-2026-06-16.md").read_text(encoding="utf-8")

scan_required = {
    "secure context computed": "const isCameraSecureContext",
    "https warning text": "手机摄像头需要 HTTPS 或 localhost",
    "field test hint": "真机扫码验收",
    "permission failure wording": "HTTPS/浏览器权限/摄像头占用",
    "secure warning render": "camera-secure-warning",
}
missing_scan = [name for name, snippet in scan_required.items() if snippet not in scan_page]
assert not missing_scan, "ScanPage missing mobile-camera readiness snippets: " + ", ".join(missing_scan)

https_required = {
    "listen ssl": "listen 443 ssl",
    "ssl cert": "ssl_certificate",
    "ssl key": "ssl_certificate_key",
    "api proxy": "proxy_pass http://backend:8000/api",
    "spa fallback": "try_files $uri $uri/ /index.html",
    "camera policy": "Permissions-Policy",
}
missing_https = [name for name, snippet in https_required.items() if snippet not in https_conf]
assert not missing_https, "nginx.https.conf missing snippets: " + ", ".join(missing_https)

compose_required = {
    "frontend https service": "frontend-https:",
    "port 8443": "8443:443",
    "cert volume": "./certs:/etc/nginx/certs:ro",
    "https conf volume": "./frontend/nginx.https.conf:/etc/nginx/conf.d/default.conf:ro",
    "depends backend": "backend",
}
missing_compose = [name for name, snippet in compose_required.items() if snippet not in compose_https]
assert not missing_compose, "docker-compose.https.yml missing snippets: " + ", ".join(missing_compose)

qr_required = {
    "zxing writer": "BrowserQRCodeSvgWriter",
    "pending receive sample": "record_DEMO_PENDING_R1",
    "received ship sample": "record_DEMO_RECEIVED_R1",
    "invalid sample": "bad_code_for_field_test",
    "output directory": "docs/acceptance/mobile-scan-samples",
}
missing_qr = [name for name, snippet in qr_required.items() if snippet not in qr_script]
assert not missing_qr, "QR sample generator missing snippets: " + ", ".join(missing_qr)

checklist_required = {
    "not yet accepted caveat": "未等于真机已通过",
    "https URL": "https://<局域网IP>:8443/scan",
    "phone permission": "允许摄像头权限",
    "sample receive": "record_DEMO_PENDING_R1",
    "sample ship": "record_DEMO_RECEIVED_R1",
    "db cross check": "DB 回查",
    "console check": "控制台无 JS error",
}
missing_checklist = [name for name, snippet in checklist_required.items() if snippet not in checklist]
assert not missing_checklist, "field checklist missing snippets: " + ", ".join(missing_checklist)

print("✅ P0 mobile camera field-readiness contract validated")
