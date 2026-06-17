#!/usr/bin/env python3
"""Validate operator-oriented scan cart UX contract in ScanPage.vue.

This is a lightweight static regression test for the H5 scan entry page:
- supermarket-like continuous scan creates editable rows
- default quantity comes from available receive/ship quantity
- rows can be edited/deleted/retried
- one-click batch submit calls receive/ship APIs
- duplicate/exception handling does not interrupt continuous scanning
- mobile camera scan is continuous, can pause/resume, and has photo/manual fallbacks
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_PAGE = ROOT / "frontend" / "src" / "views" / "ScanPage.vue"
API_FILE = ROOT / "frontend" / "src" / "api" / "records.ts"

content = SCAN_PAGE.read_text(encoding="utf-8")
api = API_FILE.read_text(encoding="utf-8")

required_snippets = {
    "cart row interface": "interface ScanCartItem",
    "cart state": "const scanCart = ref<ScanCartItem[]>([])",
    "add function": "async function addScanToCart",
    "default receive qty": "available_receive_qty",
    "default ship qty": "available_ship_qty",
    "editable quantity field": "v-model.number=\"item.qty\"",
    "delete row button": "delete-o",
    "batch submit": "async function submitCart",
    "receive API import": "receive,",
    "ship API import": "ship,",
    "record detail import": "getRecordDetail",
    "continuous camera callback": "await addScanToCart(qrCode, 'camera')",
    "photo fallback input": "accept=\"image/*\"",
    "photo capture mobile": "capture=\"environment\"",
    "photo decoder": "decodeFromImageUrl",
    "explicit getUserMedia permission": "navigator.mediaDevices?.getUserMedia",
    "decode from granted stream": "decodeFromStream(",
    "camera permission denied handling": "NotAllowedError",
    "camera error card": "camera-error-card",
    "camera status": "cameraStatus",
    "camera permission guidance": "请在浏览器地址栏允许摄像头权限",
    "rear camera constraint": "facingMode: { ideal: 'environment' }",
    "no auto route on submit scan": "addScanToCart(qrCode, 'gun')",
    "operator wording": "像超市收银一样连续扫码",
    # Plan phase 2/3 interaction details
    "working status wording": "连续扫码中，扫到码会自动加入下方清单",
    "scanned count wording": "已扫数量",
    "estimated totals wording": "本次预计接收/发出总数",
    "manual fallback": "手工输入二维码编号",
    "pause camera": "暂停扫码",
    "resume camera": "继续扫码",
    "quantity decrement": "adjustQty(item, -1)",
    "quantity increment": "adjustQty(item, 1)",
    "quantity all": "全部",
    "over receive warning": "不能超过可接收",
    "over ship warning": "不能超过可发出",
    "vibrate feedback": "navigator.vibrate",
    "duplicate locate": "重复扫码，已定位到已有行",
    "duplicate function": "findDuplicateItem",
    "row flash": "flashId",
    "exception section": "异常区",
    "exception toggle": "查看异常",
    "retry row": "retryCartItem",
    "clear completed": "清空已完成",
    "operator batch wording": "离线扫码导入",
}

missing = [name for name, snippet in required_snippets.items() if snippet not in content]
assert not missing, "ScanPage missing required scan-cart UX snippets: " + ", ".join(missing)

assert "export const receive" in api and "export const ship" in api and "export const getRecordDetail" in api
assert "routeByResult(result)" not in content, "scan page should not auto-jump after each scan in cart mode"
assert "scanBatch(" not in content, "scan cart mode should add editable rows, not only parse batch codes"
assert "批量粘贴" not in content, "scan page should avoid confusing operator wording 批量粘贴"

print("✅ scan cart UI contract validated")
