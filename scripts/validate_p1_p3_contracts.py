#!/usr/bin/env python3
"""P1-P3 后续阶段契约测试（RED -> GREEN）。

覆盖范围（飞书已取消）：
P1: 标准 MOM/文件导入接口 + 角色权限矩阵
P2: Playwright 真浏览器 E2E 资产 + 操作审计报表
P3: CI/CD 与生产化部署资产
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "backend/app/routers/mom.py",
    "backend/app/services/mom_service.py",
    "backend/app/routers/audit.py",
    "backend/app/services/audit_service.py",
    "frontend/src/views/AuditReportPage.vue",
    "tests/e2e/outsourcing-flow.spec.ts",
    "playwright.config.ts",
    ".github/workflows/ci-cd.yml",
    "docker-compose.prod.yml",
    "docs/deployment/production-deploy.md",
    "scripts/validate_role_permission_matrix.py",
    "scripts/validate_audit_report.py",
    "scripts/production_smoke_check.py",
]

FORBIDDEN_ACTIVE_FEISHU_FILES = [
    "backend/app/routers/mom.py",
    "backend/app/services/mom_service.py",
    "backend/app/main.py",
    "frontend/src/router.ts",
]

EXPECTATIONS = {
    "backend/app/main.py": [
        "include_router(mom_router)",
        "include_router(audit_router)",
    ],
    "backend/app/routers/mom.py": [
        "/orders/import",
        "MOMImportRequest",
        "source_type",
        "standard_file",
        "get_current_user",
        "require_import_permission",
    ],
    "backend/app/services/mom_service.py": [
        "import_orders",
        "created_orders",
        "updated_orders",
        "created_processes",
        "created_records",
        "source_type",
    ],
    "backend/app/routers/audit.py": [
        "/api/audit",
        "/logs",
        "/summary",
        "/export",
        "StreamingResponse",
        "get_current_user",
    ],
    "backend/app/services/audit_service.py": [
        "list_logs",
        "get_summary",
        "export_logs",
        "ActionLog",
        "openpyxl",
    ],
    "frontend/src/router.ts": [
        "'/audit'",
        "AuditReport",
        "enterprise_admin",
    ],
    "frontend/src/views/AuditReportPage.vue": [
        "操作审计报表",
        "审计总览",
        "导出审计Excel",
        "/audit/logs",
        "/audit/summary",
    ],
    "tests/e2e/outsourcing-flow.spec.ts": [
        "@playwright/test",
        "扫码",
        "看板",
        "审计",
    ],
    "playwright.config.ts": [
        "defineConfig",
        "baseURL",
        "chromium",
    ],
    ".github/workflows/ci-cd.yml": [
        "test-backend",
        "build-frontend",
        "pytest tests/",
        "npm run build",
    ],
    "docker-compose.prod.yml": [
        "restart: unless-stopped",
        "healthcheck",
        "frontend",
        "backend",
        "mysql",
    ],
    "docs/deployment/production-deploy.md": [
        "生产化部署",
        "环境变量",
        "健康检查",
        "回滚",
    ],
}


def fail(msg: str) -> None:
    raise AssertionError(msg)


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        fail(f"缺少文件: {rel}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"缺少文件: {rel}")

    for rel, snippets in EXPECTATIONS.items():
        try:
            text = read(rel)
        except AssertionError as e:
            errors.append(str(e))
            continue
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{rel} 缺少契约片段: {snippet}")

    for rel in FORBIDDEN_ACTIVE_FEISHU_FILES:
        if (ROOT / rel).exists():
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            if "feishu" in text or "飞书" in text:
                errors.append(f"{rel} 仍含飞书接入痕迹；本阶段已取消飞书需求")

    spec = read("SPEC.MD")
    if "P1 | 接入真实 MOM/飞书数据源" in spec:
        errors.append("SPEC.MD 后续优先级仍写 MOM/飞书，应改为 MOM/标准文件数据源（飞书取消）")
    if "飞书正式对接" in spec:
        errors.append("SPEC.MD 未覆盖边界仍写飞书正式对接，应标明飞书已取消")

    print(json.dumps({"total_errors": len(errors), "errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
