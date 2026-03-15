# Docker 部署

## 文件说明

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `scripts/deploy_docker.sh`

## 部署前准备

1. 服务器安装 Docker 与 Docker Compose。
2. 将项目代码上传到服务器目录，例如 `/opt/storyteller`。
3. 确认 `.env` 中的 `NOVEL_DATABASE_URL` 可从容器内访问。

当前项目会直接由 FastAPI 托管 `frontend_vue/dist`，因此只需要启动一个应用容器。

## 一键启动

```bash
cd /opt/storyteller
chmod +x scripts/deploy_docker.sh
./scripts/deploy_docker.sh
```

## 手动启动

```bash
docker compose up -d --build
```

## 查看状态

```bash
docker compose ps
docker compose logs -f storyteller
```

## 访问地址

```text
http://服务器IP:8010
```

## 说明

- 容器启动后会执行 FastAPI 的 startup 逻辑，自动创建/校正部分数据表。
- 当前编排不包含 PostgreSQL 容器，默认使用 `.env` 中配置的外部数据库。
- 如果服务器防火墙开启，需要放行 `8010` 端口。
