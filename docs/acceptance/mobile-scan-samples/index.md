# 手机摄像头扫码现场验收样张

这些二维码样张由 `scripts/generate_mobile_scan_qr_samples.mjs` 使用 `@zxing/library` 的 `BrowserQRCodeSvgWriter` 生成，用于 P0 真机扫码验收支撑。

> 注意：样张生成完成未等于真机已通过，仍需按现场清单使用手机访问 HTTPS 地址进行扫码、提交、API/DB 回查。

| 样张 | 码值 | SVG | 用途 |
| --- | --- | --- | --- |
| record_DEMO_PENDING_R1 | `record_DEMO_PENDING_R1` | [record_DEMO_PENDING_R1.svg](./record_DEMO_PENDING_R1.svg) | 待接收记录：用于真机扫码验收接收提交路径 |
| record_DEMO_RECEIVED_R1 | `record_DEMO_RECEIVED_R1` | [record_DEMO_RECEIVED_R1.svg](./record_DEMO_RECEIVED_R1.svg) | 已接收记录：用于真机扫码验收发出提交路径 |
| bad_code_for_field_test | `bad_code_for_field_test` | [bad_code_for_field_test.svg](./bad_code_for_field_test.svg) | 无效码：用于现场异常提示与不可提交路径验证 |

## 重新生成

```bash
node scripts/generate_mobile_scan_qr_samples.mjs
```
