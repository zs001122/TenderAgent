# Tender Opportunity Mining System

## 当前状态（MVP）

- MVP 功能闭环已完成：抓取 → 提取 → 入库 → 匹配 → 推荐
- 后端自动化测试基线：59 passed
- 前端最小可用界面已完成（列表、详情、公司画像）
- 工程化已完成：CI 自动化、数据库连接配置化、前端 smoke 测试
- 下一步主线：功能实现优先（API 能力扩展、业务策略增强、前端功能完善）
- 工程化工作改为配套保障项（按功能推进节奏同步完善）

## 架构概览

- **Backend**: FastAPI + SQLModel，负责数据处理与分析 API
- **Frontend**: React + Vite + TypeScript + Ant Design
- **Crawlers**: 独立抓取模块，负责多源招标采集
- **Docs/Logs**: 规划文档、开发日志、总开发日志

## 目录结构

```text
TenderAgent/
├── backend/                  # 后端服务与测试
│   ├── app/
│   ├── tests/
│   ├── scripts/
│   └── alembic/
├── frontend/                 # 前端服务
├── crawlers/                 # 爬虫模块
├── docs/                     # 模块规划与开发记录
│   ├── plans/
│   ├── dev-logs/
│   └── development/
├── scripts/                  # 运维与工具脚本
├── deploy/                   # 部署配置（逐步完善）
├── .trae/documents/          # 总规划与执行文档
└── memory.md                 # 全局开发日志（基线）
```

## 文档索引

- 总规划文档：`.trae/documents/tender_system_implementation_plan.md`
- MVP 进度与下一步计划：`.trae/documents/mvp_progress_and_next_steps_plan_2026-04-02.md`
- 模块子规划：`docs/plans/*.md`
- 模块开发记录：`docs/dev-logs/*.md`
- 全局开发日志：`memory.md`

## 本地启动

### 1) 启动后端

```bash
cd /home/wushuxin/TenderAgent/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) 启动前端

```bash
cd /home/wushuxin/TenderAgent/frontend
npm install
npm run dev
```

### 3) 初始化测试数据

```bash
cd /home/wushuxin/TenderAgent/backend
python scripts/create_test_data.py
```

### 3.1) 抓取→增量入库→分析 一次跑通

```bash
cd /home/wushuxin/TenderAgent
/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode once --scrapers cmcc,telecom --max-pages 2 --analyze-limit 200
```

### 3.2) 每日定时抓取与分析（守护模式）

```bash
cd /home/wushuxin/TenderAgent
/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode daemon --time 02:00 --scrapers cmcc,telecom --max-pages 2 --analyze-limit 500
```

说明：数据抓取管道统一使用项目虚拟环境 Python 运行（`venv/bin/python`），当前不配置 `systemd` 服务文件。

### 3.3) 抓取链路健康指标

```bash
cd /home/wushuxin/TenderAgent
python backend/scripts/health_check.py
```

该命令会输出 `health_check_ok` 与 `crawler_health` JSON（近 24 小时抓取成功率、新增数、待分析积压）。

如果需要启用电信/移动爬虫，请先安装抓取依赖与浏览器内核：

```bash
pip install -r /home/wushuxin/TenderAgent/crawlers/requirements.txt
playwright install chromium
```

### 4) 一键启动（前后端同时）

```bash
bash /home/wushuxin/TenderAgent/scripts/start_mvp.sh
```

```bash
bash /home/wushuxin/TenderAgent/scripts/start_mvp.sh status
```

```bash
bash /home/wushuxin/TenderAgent/scripts/start_mvp.sh stop
```

```bash
bash /home/wushuxin/TenderAgent/scripts/start_mvp.sh restart
```

端口冲突时可临时指定端口：

```bash
BACKEND_PORT=8010 FRONTEND_PORT=3010 bash /home/wushuxin/TenderAgent/scripts/start_mvp.sh start
```

默认端口被占用时，脚本会自动切换到可用端口，并在输出中打印实际 `backend_url` 与 `frontend_url`。

访问地址：
- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

## 关键 API（新增）

- `POST /api/tenders/analyze-batch`：批量分析（返回成功数、失败数、失败明细、可重试 ID）
- `POST /api/feedback/bid`：记录投标反馈
- `PUT /api/feedback/result/{record_id}`：更新投标结果
- `GET /api/feedback/stats`：反馈学习准确率统计
- `GET /api/dashboard/crawler-health?hours=24`：抓取链路健康指标
