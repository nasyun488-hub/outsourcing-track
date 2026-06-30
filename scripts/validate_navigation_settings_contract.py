#!/usr/bin/env python3
"""快捷导航与设置中心静态契约验证。

目标：所有次级页面都有主页/快捷操作入口；系统有设置中心，集中承载用户设置、人员账户、权限说明、密码管理。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"
VIEWS = SRC / "views"

SECONDARY_PAGES = [
    "ScanPage.vue",
    "KanbanPage.vue",
    "KanbanDetailPage.vue",
    "ReceivePage.vue",
    "ShipPage.vue",
    "RecordViewPage.vue",
    "NotificationPage.vue",
    "AuditReportPage.vue",
    "ExportPage.vue",
    "AdminUserPage.vue",
    "AdminFactoryPage.vue",
]

REQUIRED_SECONDARY_MARKERS = [
    "页面快捷操作",
    "回到主页",
    "设置中心",
    "router.push('/')",
    "router.push('/settings')",
]

CHECKS: dict[str, list[str]] = {
    "router.ts": [
        "path: '/settings'",
        "name: 'Settings'",
        "SettingsPage.vue",
        "requiresAuth: true",
    ],
    "App.vue": [
        "设置中心",
        "path: '/settings'",
    ],
    "views/HomePage.vue": [
        "系统设置",
        "goToSettings",
        "router.push('/settings')",
    ],
    "views/SettingsPage.vue": [
        "设置中心",
        "用户设置",
        "人员账户管理",
        "权限设置",
        "密码管理",
        "当前登录用户",
        "router.push('/admin/users')",
        "router.push('/')",
        "修改密码",
        "保存设置",
    ],
}


def read(relative: str) -> str:
    path = SRC / relative
    if not path.exists():
        raise AssertionError(f"文件不存在: frontend/src/{relative}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    failures: list[str] = []

    for relative, needles in CHECKS.items():
        try:
            text = read(relative)
        except AssertionError as exc:
            failures.append(str(exc))
            continue
        for needle in needles:
            if needle not in text:
                failures.append(f"frontend/src/{relative}: 缺少 `{needle}`")

    for filename in SECONDARY_PAGES:
        path = VIEWS / filename
        if not path.exists():
            failures.append(f"frontend/src/views/{filename}: 文件不存在")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in REQUIRED_SECONDARY_MARKERS:
            if marker not in text:
                failures.append(f"frontend/src/views/{filename}: 缺少快捷导航标记 `{marker}`")

    if failures:
        print("Navigation/settings contract FAILED")
        for failure in failures:
            print("-", failure)
        return 1

    print("Navigation/settings contract OK")
    print(f"checked_secondary_pages={len(SECONDARY_PAGES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
