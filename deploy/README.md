# 部署说明（最小可交付）

## 运行方式

当前采用单机方式部署，前后端分离启动：

1. 启动后端（FastAPI）
2. 启动前端（Vite）
3. 通过环境变量配置数据库连接与运行模式

## 环境变量

- `DATABASE_URL`：数据库连接串，默认使用 SQLite
- `DB_ECHO`：SQL 日志开关，`true` 或 `false`
- `BACKEND_HOST`：后端监听地址，默认 `0.0.0.0`
- `BACKEND_PORT`：后端监听端口，默认 `8000`
- `FRONTEND_PORT`：前端端口，默认 `3000`

## 启动命令

```bash
cd /home/wushuxin/TenderAgent/backend && pip install -r requirements.txt && python -m uvicorn app.main:app --reload --host ${BACKEND_HOST:-0.0.0.0} --port ${BACKEND_PORT:-8000}
```

```bash
cd /home/wushuxin/TenderAgent/frontend && npm install && npm run dev -- --host 0.0.0.0 --port ${FRONTEND_PORT:-3000}
```

## 发布前检查

```bash
cd /home/wushuxin/TenderAgent/backend && pytest
```

```bash
cd /home/wushuxin/TenderAgent/frontend && npm run build
```
