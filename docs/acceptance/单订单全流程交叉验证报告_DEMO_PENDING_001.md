# 单订单全流程交叉验证报告：DEMO_PENDING_001

生成时间：2026-06-11 22:26

## 结论

以订单 `DEMO_PENDING_001` 为样本，按“数据先行 → 规则梳理 → 场景矩阵 → API 实测 → DB 回查 → 交叉比对”的方式完成全流程验证。

**总体结论：主流程通过，发现 1 个业务闭环边界问题。**

- API 调用成功：通过
- DB 状态回写：通过
- 上下道数量约束：通过
- 超量拦截：通过
- 无关厂家权限隔离：通过
- API 与 DB 数量一致：通过
- 通知乱码：通过
- 订单完结状态：存在边界问题，三道工序均已发出后订单仍为 `in_progress`

## 测试订单基线

| 字段 | 值 |
|---|---|
| 订单ID | DEMO_PENDING_001 |
| 总数量 | 80 |
| 初始订单状态 | pending |
| 工序数 | 3 |

| 顺序 | 工序 | 记录ID | 厂家 | 初始状态 | 初始锁 | 收 | 发 |
|---:|---|---|---|---|---|---:|---:|
| 1 | 首道精加工 | DEMO_PENDING_R1 | F002 | pending | none | 0 | 0 |
| 2 | 二道热处理 | DEMO_PENDING_R2 | F003 | pending | none | 0 | 0 |
| 3 | 末道总装终检 | DEMO_PENDING_R3 | F001 | pending | none | 0 | 0 |

## 场景验证结果

| 编号 | 场景 | 预期 | HTTP | DB 回查 | 结论 |
|---|---|---|---:|---|---|
| A0 | 看板工序详情字段 | 返回3道工序，含可接收/可发出字段 | 200 | 字段存在 | 通过 |
| P1 | 无关厂家详情权限隔离 | F004 无参与关系应 403 | 403 | 无 DB 变更 | 通过 |
| C1 | 下道提前接收拦截 | R1 未发出，R2 接收应拒绝 | 400 | R2 收/发仍为0 | 通过 |
| A1 | 首道正常接收 | R1 receive=80，订单进入进行中 | 200 | R1 收=80，状态 received | 通过 |
| C2 | 首道超量发出拦截 | R1 已收80，ship 81 应拒绝 | 400 | R1 发仍为0 | 通过 |
| A2 | 首道正常发出 | R1 ship=80，下道可接收80 | 200 | R1 发=80，状态 shipped | 通过 |
| A3 | 二道正常接收 | R2 receive=80，不超过 R1 ship | 200 | R2 收=80；R1 锁转 relation_lock | 通过 |
| A4 | 二道正常发出 | R2 ship=80，末道可接收80 | 200 | R2 发=80，状态 shipped | 通过 |
| A5 | 末道正常接收 | R3 receive=80，不超过 R2 ship | 200 | R3 收=80；R2 锁转 relation_lock | 通过 |
| A6 | 末道正常发出 | R3 ship=80，全订单流转完成 | 200 | 三道发出均=80 | 主流程通过，但订单状态未完结 |
| X1 | API 与 DB 数量交叉一致 | 看板 API receive/ship 与 DB 一致 | 200 | 三道均一致 | 通过 |
| X2 | 通知中文乱码检查 | 乱码计数=0 | 200 | mojibake_count=0 | 通过 |

## 最终 DB 状态

| 顺序 | 工序 | 记录ID | 状态 | 锁 | 收 | 发 |
|---:|---|---|---|---|---:|---:|
| 1 | 首道精加工 | DEMO_PENDING_R1 | shipped | relation_lock | 80 | 80 |
| 2 | 二道热处理 | DEMO_PENDING_R2 | shipped | relation_lock | 80 | 80 |
| 3 | 末道总装终检 | DEMO_PENDING_R3 | shipped | entry_lock | 80 | 80 |

最终订单状态：`in_progress`

## 发现的问题

### Bug-001：三道工序全部发出后，订单未自动完结

**严重级别：中**

**现象：**
- 三道工序均已完成接收与发出：`receive=80 / ship=80`
- API 与 DB 数量一致
- 但 `orders.order_status` 仍为 `in_progress`

**影响：**
- 看板上该订单仍显示进行中
- 业务闭环缺少“完结/归档”状态
- 后续统计中已完成订单数可能偏低

**建议修复：**
- 在末道工序发出成功后，如果该订单全部工序 `total_ship_qty >= order.total_qty`，则：
  - 将订单状态更新为 `completed`
  - 末道记录状态可更新为 `completed` 或保持 `shipped` 但订单需 completed
  - 末道锁状态建议转为 `sync_lock` 或明确终态锁
- 补充回归场景：末道发出后校验 `orders.order_status = completed`

## 验证原始证据

完整 JSON 证据文件：

`/home/takemehome/outsourcing-track/docs/acceptance/single-order-cross-validation.json`

## 最终判断

- **后端/API/DB 主流转链路：通过**
- **权限与数量约束：通过**
- **通知中文与 API 字段：通过**
- **订单业务完结闭环：未完全通过，需要补自动完结逻辑**
