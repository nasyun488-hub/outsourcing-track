# 单订单全流程交叉验证报告：DEMO_PENDING_001（修复后）

生成时间：2026-06-11 22:40

## 结论

以订单 `DEMO_PENDING_001` 为样本，按“数据先行 → 场景矩阵 → API 实测 → DB 回查 → API/DB 交叉比对”的方式重新验证。

**最终结论：全部通过。**

上一轮发现的问题“三道工序全部发出后订单仍为 `in_progress`”已修复。

## 本轮修复

文件：`backend/app/services/record_service.py`

修复点：
- `_update_order_status()` 不再只依赖 `record_status == completed`
- 改为以业务数量闭环判断终态：所有工序 `total_ship_qty >= order.total_qty` 时，订单自动置为 `completed`
- 同步将三道工序置为：
  - `record_status = completed`
  - `lock_type = sync_lock`
- 保留动作日志写入

## 验证样本

| 字段 | 值 |
|---|---|
| 订单ID | DEMO_PENDING_001 |
| 总数量 | 80 |
| 工序数 | 3 |
| 初始状态 | pending |

初始工序：

| 顺序 | 工序 | 记录ID | 厂家 | 初始状态 | 初始锁 | 收 | 发 |
|---:|---|---|---|---|---|---:|---:|
| 1 | 首道精加工 | DEMO_PENDING_R1 | F002 | pending | none | 0 | 0 |
| 2 | 二道热处理 | DEMO_PENDING_R2 | F003 | pending | none | 0 | 0 |
| 3 | 末道总装终检 | DEMO_PENDING_R3 | F001 | pending | none | 0 | 0 |

## 场景结果

| 编号 | 场景 | 预期 | 结果 |
|---|---|---|---|
| H0 | 后端健康检查 | `/health` 返回 200 | 通过 |
| A0 | 看板工序详情字段 | 3 道工序，含可接收/可发出字段 | 通过 |
| P1 | 无关厂家权限隔离 | F004 无参与关系，详情应 403 | 通过 |
| C1 | 下道提前接收拦截 | R1 未发出时 R2 接收应拒绝 | 通过 |
| A1 | 首道正常接收 | R1 收 80，订单进入 in_progress | 通过 |
| C2 | 首道超量发出拦截 | R1 已收 80，发 81 应拒绝 | 通过 |
| A2 | 首道正常发出 | R1 发 80，下道可接收 80 | 通过 |
| A3 | 二道正常接收 | R2 收 80，R1 锁转 relation_lock | 通过 |
| A4 | 二道正常发出 | R2 发 80，末道可接收 80 | 通过 |
| A5 | 末道正常接收 | R3 收 80，R2 锁转 relation_lock | 通过 |
| A6 | 末道正常发出/订单完结 | R3 发 80 后订单 completed | 通过 |
| X1 | API 与 DB 交叉一致 | 看板 API 数量/状态与 DB 一致 | 通过 |
| X2 | 通知乱码检查 | 乱码计数 0 | 通过 |

## 最终 DB 状态

| 顺序 | 记录ID | 状态 | 锁 | 收 | 发 |
|---:|---|---|---|---:|---:|
| 1 | DEMO_PENDING_R1 | completed | sync_lock | 80 | 80 |
| 2 | DEMO_PENDING_R2 | completed | sync_lock | 80 | 80 |
| 3 | DEMO_PENDING_R3 | completed | sync_lock | 80 | 80 |

最终订单状态：`completed`

## 构建与部署验证

| 项 | 结果 |
|---|---|
| Python 编译 | 通过 |
| backend 镜像构建 | 通过 |
| backend 容器重启 | 通过 |
| `/health` | 200 |
| 单订单交叉验证 | 13 项全部通过 |

## 原始证据

JSON 证据文件：

`/home/takemehome/outsourcing-track/docs/acceptance/single-order-cross-validation-after-fix.json`

## 最终判断

- **后端/API/DB 主流程：通过**
- **订单自动完结闭环：通过**
- **权限隔离：通过**
- **数量约束与超量拦截：通过**
- **通知中文：通过**
- **前端体验：此前已完成移动端关键页面改造，本轮未新增视觉重构**
