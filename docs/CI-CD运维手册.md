# 外协工序流转追踪系统 - CI/CD 运维手册

**版本**: v1.0  
**日期**: 2026-06-18

---

## 一、CI/CD 流程概览

```
代码提交到 GitHub
    ↓
GitHub Actions 自动触发
    ↓
├─ 后端 pytest 测试 (MySQL 8.0)
│  └─ auth + kanban 共 13 个用例
├─ 前端构建检查
│  └─ npm run build
    ↓
测试通过 → 构建 Docker 镜像 → 推送到 GHCR
    ↓
(后续服务器就绪后) → 自动部署到生产环境
```

---

## 二、GitHub 仓库信息

| 项目 | 值 |
|------|----|
| 仓库地址 | `https://github.com/[您的用户名]/outsourcing-track` |
| CI 配置 | `.github/workflows/ci-cd.yml` |
| 镜像仓库 | `ghcr.io/[您的用户名]/outsourcing-track-backend` |
| | `ghcr.io/[您的用户名]/outsourcing-track-frontend` |

---

## 三、首次推送代码

```bash
# 1. 添加远程仓库
git remote add origin https://github.com/[您的用户名]/outsourcing-track.git

# 2. 分支重命名为 main (如果当前是 master)
git branch -M main

# 3. 首次推送
git push -u origin main

# 4. 查看 CI 运行状态
# 浏览器访问: https://github.com/[您的用户名]/outsourcing-track/actions
```

首次推送后，GitHub Actions 会自动运行：
- ✅ 后端 pytest 测试
- ✅ 前端构建检查
- ✅ 构建并推送 Docker 镜像

---

## 四、生产环境部署步骤

### 前置条件
1. 服务器已安装 Docker + Docker Compose
2. 服务器能访问 GitHub Container Registry (ghcr.io)
3. 已开放所需端口（默认 8080 前端, 8000 后端, 3306 MySQL）

### 部署步骤

```bash
# 1. 登录 GHCR (在服务器上执行)
docker login ghcr.io -u [您的GitHub用户名]
# 密码使用您的 GitHub PAT

# 2. 创建部署目录
mkdir -p /opt/outsourcing-track
cd /opt/outsourcing-track

# 3. 复制生产配置模板
wget https://raw.githubusercontent.com/[您的用户名]/outsourcing-track/main/docker-compose.prod.template.yml
cp docker-compose.prod.template.yml docker-compose.yml

# 4. 编辑配置，修改密码和端口
vi docker-compose.yml
# 必须修改:
#   - MYSQL_ROOT_PASSWORD
#   - SECRET_KEY
#   - GITHUB_USERNAME

# 5. 拉取镜像并启动
docker compose pull
docker compose up -d

# 6. 检查服务状态
docker compose ps
docker compose logs -f
```

---

## 五、日常运维命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql

# 手动更新到最新版本
docker compose pull
docker compose up -d

# 重启服务
docker compose restart backend
docker compose restart frontend

# 数据库备份
docker exec outsourcing-mysql mysqldump -uroot -p[密码] outsourcing_track > backup_$(date +%Y%m%d).sql

# 数据库恢复
docker exec -i outsourcing-mysql mysql -uroot -p[密码] outsourcing_track < backup_20260618.sql
```

---

## 六、常见问题排查

### 问题 1: CI 测试失败
- 访问: https://github.com/[您的用户名]/outsourcing-track/actions
- 点击失败的 workflow run，查看具体哪个 Job 失败
- 常见原因：
  - 新增代码引入 bug
  - 数据库迁移脚本有问题
  - 依赖包版本冲突

### 问题 2: 镜像拉取失败
```bash
# 检查是否登录 GHCR
docker login ghcr.io

# 检查镜像是否存在
docker pull ghcr.io/[您的用户名]/outsourcing-track-backend:latest
```

### 问题 3: 后端连不上数据库
- 检查 MySQL 容器是否健康: `docker compose ps mysql`
- 检查 `docker-compose.yml` 中数据库密码是否一致
- 查看后端日志: `docker compose logs backend`

### 问题 4: 前端页面 404
- 检查 nginx 配置: `frontend/nginx.conf`
- 检查前端容器是否正常: `docker compose ps frontend`
- 查看前端日志: `docker compose logs frontend`

---

## 七、手动回滚步骤

如果新版本有问题，快速回滚到上一个版本：

```bash
# 1. 查看可用镜像
docker images ghcr.io/[您的用户名]/outsourcing-track-backend

# 2. 用特定 SHA 启动（用前一个成功的版本）
# 修改 docker-compose.yml 中的 image 标签
# image: ghcr.io/[您的用户名]/outsourcing-track-backend:sha-xxxxxxx

# 3. 重启
docker compose up -d
```

---

## 八、开启自动部署（后续服务器就绪后）

需要在 GitHub 仓库 Settings 中配置：

1. 创建 Environment: `production`
2. 添加以下 Secrets:
   - `SERVER_HOST`: 服务器 IP
   - `SERVER_USER`: SSH 用户名
   - `SSH_PRIVATE_KEY`: SSH 私钥
3. 取消 CI 配置中 deploy job 的注释
4. 后续合并到 main 分支会自动部署

---

## 九、CI 配置说明

| Job 名称 | 触发条件 | 耗时 | 说明 |
|---------|---------|------|------|
| test-backend | 每次 push/PR | ~2 分钟 | 后端 pytest 13 个用例 |
| build-frontend | 每次 push/PR | ~3 分钟 | 前端构建检查 |
| build-and-push-images | 仅 main 分支，测试通过后 | ~5 分钟 | 构建并推送 Docker 镜像 |
| deploy | 仅 main 分支，镜像构建后（当前禁用） | ~1 分钟 | SSH 自动部署到服务器 |

---

## 十、后续优化建议

1. **HTTPS**: 配置 Nginx 反向代理 + Let's Encrypt 证书
2. **监控**: 接入 Prometheus + Grafana 监控
3. **日志聚合**: ELK 或 Loki 日志系统
4. **性能测试**: 集成 k6 接口压力测试
5. **代码质量**: SonarQube 代码质量扫描
6. **漏洞扫描**: Trivy 镜像漏洞扫描