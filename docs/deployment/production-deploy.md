# 生产化部署

本文档描述外协工序流转追踪系统的生产部署流程，数据源采用 MOM/标准文件导入。

## 环境变量

在服务器创建 `.env`，不要提交到仓库：

```env
MYSQL_ROOT_PASSWORD=<强随机密码>
MYSQL_DATABASE=outsourcing_track
MYSQL_USER=outsourcing_app
MYSQL_PASSWORD=<强随机密码>
SECRET_KEY=<JWT强随机密钥>
FRONTEND_PORT=80
SMS_PROVIDER=mock
```

## 首次部署

```bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH
docker compose -f docker-compose.prod.yml --env-file .env build
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

## 健康检查

```bash
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${FRONTEND_PORT:-80}/ >/dev/null
curl -fsS http://127.0.0.1:8000/health
python3 scripts/production_smoke_check.py --base-url http://127.0.0.1:${FRONTEND_PORT:-80}
```

## 数据导入与审计

- 管理员通过 `POST /api/mom/orders/import` 导入 MOM 标准 JSON/文件解析结果。
- 导入会写入 `orders`、`processes`、`process_records`，并在 `action_logs` 记录 `MOM_IMPORT`。
- 审计页面 `/audit` 可查看审计总览、日志列表并导出审计 Excel。

## 回滚

1. 保留当前镜像与数据库卷快照。
2. 如新版本异常，执行：
   ```bash
   docker compose -f docker-compose.prod.yml down
   git checkout <last-good-tag>
   docker compose -f docker-compose.prod.yml --env-file .env up -d --build
   ```
3. 若涉及数据迁移，先从备份恢复 MySQL，再启动服务。

## 运维注意

- 定期备份 `mysql_prod_data`。
- `SECRET_KEY`、数据库密码必须由环境变量提供，禁止硬编码。
- 对外建议放置 HTTPS 网关或云负载均衡，并限制数据库端口不暴露公网。
