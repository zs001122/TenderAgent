# 数据库设计与每日增量更新方案

## 1. 需求分析
用户希望在第一阶段基础架构搭建中，规划并实施一个支持每日增量更新的数据库方案。数据内容主要为招标公告，涉及网址渠道、公告类型、标题、发布日期等字段。

## 2. 数据库选型
考虑到招标公告数据的特性（结构化元数据 + 非结构化全文内容）以及后续的全文检索和分析需求，建议采用 **PostgreSQL**。
- **PostgreSQL**: 适合存储结构化数据（标题、日期、渠道）和 JSONB 数据（灵活的扩展字段），且具备良好的全文检索能力。
- **向量数据库 (可选)**: 如果后续需要基于语义搜索相似公告，可以引入 pgvector 插件。

## 3. 表结构设计 (Schema Design)

### 3.1 核心表：`tenders` (招标公告表)
这是存储公告主体信息的表。

| 字段名 | 类型 | 说明 | 约束 |
| :--- | :--- | :--- | :--- |
| `id` | UUID/BIGINT | 主键 | Primary Key, Auto Increment |
| `source_url` | TEXT | 公告原始链接 | Unique, Not Null (用于去重) |
| `source_site` | VARCHAR(50) | 来源渠道/网站 | Not Null (e.g., "中国电信", "中国移动") |
| `title` | TEXT | 公告标题 | Not Null |
| `publish_date` | DATE | 发布日期 | Not Null, Index (用于按时间查询) |
| `notice_type` | VARCHAR(50) | 公告类型 | Index (e.g., "招标公告", "中标候选人公示") |
| `content` | TEXT | 公告正文内容 | (可能非常长) |
| `budget_amount` | DECIMAL(15,2) | 预算金额 (标准化后) | Nullable |
| `region` | VARCHAR(50) | 省份/地区 | Index |
| `created_at` | TIMESTAMP | 抓取入库时间 | Default Now() |
| `updated_at` | TIMESTAMP | 更新时间 | Default Now() |

### 3.2 辅助表：`crawl_logs` (抓取日志表)
用于记录每次增量更新的状态，确保数据完整性。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | BIGINT | 主键 |
| `source_site` | VARCHAR(50) | 来源站点 |
| `start_time` | TIMESTAMP | 开始时间 |
| `end_time` | TIMESTAMP | 结束时间 |
| `new_count` | INT | 新增数量 |
| `update_count` | INT | 更新数量 |
| `status` | VARCHAR(20) | 状态 (SUCCESS/FAILED) |

## 4. 每日增量更新策略

### 4.1 去重机制 (Deduplication)
- **基于 URL 去重**: `source_url` 字段设为唯一索引。每次插入前检查 URL 是否存在。
- **Upsert (Insert on Conflict)**: 使用 SQL 的 `INSERT ... ON CONFLICT (source_url) DO NOTHING`。

### 4.2 增量抓取流程
1.  **采集前置判断**: 采集前先查询数据库中该渠道最新的 `publish_date`。
2.  **数据比对**: 抓取过程中，遇到已存在于数据库的 URL 且发布时间较早，则停止继续往后抓取。
3.  **定时触发**: 使用 APScheduler 或系统 Crontab 每天定时运行爬虫。

## 5. 实施步骤

### 步骤 1: 环境与依赖
- 安装 PostgreSQL。
- 安装 `sqlmodel` 或 `sqlalchemy`。
- 配置 `alembic` 进行数据库迁移管理。

### 步骤 2: 定义 ORM 模型
- 在 `backend/app/models/` 下创建模型类。

### 步骤 3: 改造 Repository
- 将 `TenderRepository` 从 CSV 模式切换为 SQL 模式。
- 实现增量保存逻辑。

### 步骤 4: 改造爬虫
- 爬虫脚本调用 API 或 Repository 直接入库，不再依赖中间 CSV 文件。

## 6. 待办事项
- [ ] 确定 PostgreSQL 安装环境（本地或 Docker）。
- [ ] 初始化 Alembic 迁移脚本。
- [ ] 编写历史 CSV 数据入库脚本。
