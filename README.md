# Tender Opportunity Mining System

## 当前状态（MVP + 公司资料证据工作台）

- MVP 功能闭环已完成：抓取 → 提取 → 入库 → 匹配 → 推荐
- 公司资料证据工作台已落地：Excel 预览确认导入、资料库分页筛选、手工 CRUD、软删除/恢复、校验问题展示
- 匹配引擎已升级为证据化输出：`matching_details` 持久化 Gate 证据、资料命中、缺失项、风险项和维度评分
- 后端自动化测试基线：64 passed
- 前端生产构建通过：`npm run build`
- 当前主线：收口公司资料证据体系、保持测试和文档状态同步，再继续推进部署运维与抓取稳定性

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
├── docs/                     # 架构、规划、开发记录与归档文档
│   ├── architecture/
│   ├── plans/
│   ├── dev-logs/
│   └── archive/
├── scripts/                  # 运维与工具脚本
├── deploy/                   # 部署配置（逐步完善）
├── .archive/                 # 历史代码与手动测试脚本
├── .trae/documents/          # 总规划与执行文档
└── memory.md                 # 全局开发日志（基线）
```

## 文档索引

- 当前计划板：`.trae/documents/current_plan_board.md`
- 总规划文档：`.trae/documents/tender_system_implementation_plan.md`
- MVP 进度与下一步计划：`.trae/documents/mvp_progress_and_next_steps_plan_2026-04-02.md`
- 模块子规划：`docs/plans/*.md`
- 模块开发记录：`docs/dev-logs/*.md`
- 当前目录规范：`docs/architecture/project_structure.md`
- 旧规划与历史说明：`docs/archive/`
- 全局开发日志：`memory.md`

说明：日常查看项目当前状态时，优先参考“当前计划板”与 `memory.md`；旧阶段性规划文档保留作背景参考。

## 本地启动

### Windows / PowerShell 一键启动

```powershell
.\scripts\start_mvp.ps1 start
```

```powershell
.\scripts\start_mvp.ps1 status
.\scripts\start_mvp.ps1 stop
.\scripts\start_mvp.ps1 restart
```

默认使用后端 `8000`、前端 `3000`。如果端口被占用，脚本会自动顺延选择可用端口，并输出实际访问地址。

也可以临时指定端口：

```powershell
$env:BACKEND_PORT=8010
$env:FRONTEND_PORT=3010
.\scripts\start_mvp.ps1 start
```

脚本会自动创建 `venv`、安装后端依赖，并在首次启动前安装前端依赖。npm 缓存写入 `.runtime/npm-cache`，避免使用系统目录缓存导致权限问题。

Windows 脚本默认不启用后端热重载，以避免部分 Windows 权限环境下 `uvicorn --reload` 创建子进程失败。需要热重载时可设置：

```powershell
$env:BACKEND_RELOAD=1
.\scripts\start_mvp.ps1 restart
```

### Linux / WSL 手动启动

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

### 3.1) 抓取→增量入库 一次跑通（不自动分析）

```bash
cd /home/wushuxin/TenderAgent
/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode once --scrapers cmcc,telecom --max-pages 2
```

### 3.2) 每日定时抓取（守护模式，不自动分析）

```bash
cd /home/wushuxin/TenderAgent
/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode daemon --time 02:00 --scrapers cmcc,telecom --max-pages 2
```

说明：数据抓取管道统一使用项目虚拟环境 Python 运行（`venv/bin/python`），当前不配置 `systemd` 服务文件；分析改为手动触发（前端“重新分析”或相关分析 API）。

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
