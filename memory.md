# 招标商机挖掘系统 - 开发日志

## 2026-03-31

### 14:27 - 目录结构重构完成
**操作内容**：
- 删除 `Scrapling/` 第三方库源码
- 归档 `legacy/` 旧代码到 `.archive/`
- 删除临时文件（`1`、`scraper.log`）
- 创建新目录结构：
  - `backend/app/core/` - 核心配置
  - `backend/app/agents/` - AI Agent 系统
  - `backend/app/utils/` - 工具函数
  - `backend/tests/` - 后端测试
  - `crawlers/` - 独立的爬虫模块
  - `data/raw/` - 原始数据（按来源分类）
  - `data/processed/` - 处理后数据
  - `data/attachments/` - 附件文件
  - `docs/` - 文档（按类型分类）
  - `scripts/` - 运维脚本
  - `deploy/` - 部署配置
- 更新导入路径
- 创建配置文件：
  - `.env.example` - 环境变量模板
  - `backend/requirements.txt` - 后端依赖
  - `crawlers/requirements.txt` - 爬虫依赖
  - `backend/app/core/config.py` - 配置管理模块

**新目录结构**：
```
TenderAgent/
├── backend/          # 后端服务
├── crawlers/         # 爬虫模块（独立）
├── frontend/         # 前端服务
├── data/             # 数据存储
├── docs/             # 文档
├── scripts/          # 运维脚本
├── tests/            # 集成测试
├── deploy/           # 部署配置
└── .env.example      # 环境变量模板
```

### 14:30 - 架构优化讨论
**用户反馈要点**：
1. 信息提取需要升级为"多阶段抽取 pipeline"
   - 第一阶段：粗抽（Recall优先）
   - 第二阶段：归一化（Normalization）
   - 第三阶段：交叉验证（Consistency Check）

2. 匹配算法需要改为"Gate + Ranking"双层结构
   - Step 1：硬性过滤（Gate）- 资质、地域、时间
   - Step 2：软评分（Ranking）- 经验、预算、历史
   - Step 3：策略层（Decision）- 推荐/不投/观望

3. Agent 设计需要增加 Orchestrator（调度+决策 Agent）
   - 多Agent分析 → 单Agent决策

4. 需要增加"反馈学习闭环"
   - 推荐 → 投标 → 是否中标 → 反馈 → 优化模型

5. 知识图谱应该轻量化
   - 资质映射图谱
   - 行业分类图谱
   - 公司-中标关系

**优先级调整**：
- 🥇 第一优先级：信息提取稳定性、Gate + Ranking 双层匹配、公司画像结构化
- 🥈 第二优先级：Orchestrator Agent、附件解析增强、中标概率模型
- 🥉 第三优先级：知识图谱、复杂深度学习模型、多Agent协同

### 14:35 - 实施计划优化升级
**操作内容**：
- 根据用户反馈，对实施计划进行重大升级
- 核心升级点：
  1. 信息提取：单次抽取 → 多阶段抽取 Pipeline（粗抽 → 归一化 → 交叉验证）
  2. 匹配算法：加权评分 → Gate + Ranking 双层结构（硬门槛 + 软评分）
  3. Agent设计：多Agent分析 → Orchestrator 决策 Agent
  4. 新增反馈学习闭环：推荐 → 投标 → 中标 → 优化
  5. 知识图谱：重图谱 → 轻量级图谱

**更新文件**：
- `.trae/documents/tender_system_implementation_plan.md` - 实施计划 v2.0

### 15:00 - 第一阶段实施完成 ✅

#### 任务 1.1：多阶段信息抽取 Pipeline ✅
**新建文件**：
- `backend/app/services/extraction/__init__.py` - 模块入口
- `backend/app/services/extraction/models.py` - 数据模型（ExtractedInfo, ExtractionResult等）
- `backend/app/services/extraction/rough_extractor.py` - 粗抽模块
- `backend/app/services/extraction/normalizer.py` - 归一化模块
- `backend/app/services/extraction/validator.py` - 交叉验证模块
- `backend/app/services/extraction/pipeline.py` - 主管道

**功能说明**：
- **RoughExtractor**: 支持多种预算格式（万元/元/亿元）、日期格式、资质提取、联系人提取
- **FieldNormalizer**: 资质名称标准化、预算归一化、地区归一化
- **ConsistencyValidator**: 正文与附件一致性检查、数据有效性验证

#### 任务 1.2：Gate + Ranking 双层匹配算法 ✅
**新建文件**：
- `backend/app/services/matching/__init__.py` - 模块入口
- `backend/app/services/matching/gate_filter.py` - 硬性过滤层
- `backend/app/services/matching/ranking_engine.py` - 软评分层
- `backend/app/services/matching/matching_engine.py` - 匹配引擎

**功能说明**：
- **GateFilter**: 资质门槛检查、地域门槛检查、时间门槛检查、预算范围检查
- **RankingEngine**: 经验匹配评分、预算匹配评分、历史中标概率、竞争程度评估
- **MatchingEngine**: Gate过滤 → Ranking评分 → 决策输出

#### 任务 1.3：Orchestrator 决策 Agent ✅
**新建文件**：
- `backend/app/agents/__init__.py` - 模块入口
- `backend/app/agents/base_agent.py` - Agent基类
- `backend/app/agents/qualification_agent.py` - 资质分析Agent
- `backend/app/agents/risk_agent.py` - 风险评估Agent
- `backend/app/agents/competition_agent.py` - 竞争分析Agent
- `backend/app/agents/orchestrator.py` - 决策编排Agent

**功能说明**：
- **QualificationAgent**: 分析资质匹配情况，识别缺失资质
- **RiskAgent**: 时间风险、预算风险、技术风险、竞争风险评估
- **CompetitionAgent**: 竞争程度评估、中标概率预估
- **OrchestratorAgent**: 协调多Agent分析，做出最终决策（投标/不投标/评估后决定）

#### 任务 1.4：反馈学习闭环 ✅
**新建文件**：
- `backend/app/models/feedback.py` - 数据模型（BidRecord, FeedbackAnalysis）
- `backend/app/services/feedback_learner.py` - 反馈学习服务

**功能说明**：
- **BidRecord**: 记录投标行为和结果
- **FeedbackLearner**: 记录投标、记录结果、触发优化、分析预测准确性

#### 任务 1.5：轻量级知识图谱 ✅
**新建文件**：
- `backend/app/knowledge/__init__.py` - 模块入口
- `backend/app/knowledge/qualification_mapping.py` - 资质映射图谱
- `backend/app/knowledge/industry_classification.py` - 行业分类图谱
- `backend/app/knowledge/company_relation.py` - 公司关系图谱

**功能说明**：
- **QualificationMapping**: 资质名称标准化、等价判断、别名查询
- **IndustryClassification**: 行业分类树、关键词分类、路径查询
- **CompanyRelationGraph**: 竞争对手分析、中标率统计、竞争态势分析

---

### 16:30 - 集成测试完成 ✅

**新建测试文件**：
- `backend/tests/conftest.py` - pytest 配置和 fixtures
- `backend/tests/test_extraction.py` - 信息抽取 Pipeline 测试
- `backend/tests/test_matching.py` - 匹配引擎测试
- `backend/tests/test_agents.py` - Agent 系统测试
- `backend/tests/test_e2e.py` - 端到端集成测试

**测试覆盖范围**：
1. **信息抽取测试** (13个测试)
   - 预算提取：万元/元/亿元格式
   - 日期提取：多种日期格式
   - 资质提取：资质要求识别
   - 联系人提取：姓名/电话/邮箱
   - 关键词提取：行业标签
   - Pipeline 集成：完整流程测试

2. **匹配引擎测试** (13个测试)
   - Gate 过滤层：资质/地域/时间/预算门槛
   - Ranking 评分层：多维度评分
   - 匹配引擎：Gate → Ranking → Decision 流程

3. **Agent 系统测试** (17个测试)
   - QualificationAgent：资质分析
   - RiskAgent：风险评估
   - CompetitionAgent：竞争分析
   - OrchestratorAgent：决策编排

4. **端到端测试** (8个测试)
   - 完整流程：抽取 → 匹配 → 决策
   - 批量处理
   - 知识图谱集成
   - 反馈学习集成

**测试结果**：
```
============================== 51 passed in 0.33s ==============================
```

**依赖更新**：
- `backend/requirements.txt` 添加 pytest>=7.0.0, pytest-asyncio>=0.21.0

---

### 17:30 - 文档体系建立 ✅

**新建目录结构**：
```
docs/
├── plans/                    # 子规划文档目录
│   ├── 01_extraction_pipeline.md
│   ├── 02_matching_engine.md
│   ├── 03_agent_system.md
│   ├── 04_feedback_learning.md
│   ├── 05_knowledge_graph.md
│   └── 06_crawler_system.md    # 新增
└── dev-logs/                 # 开发记录文档目录
    ├── extraction_dev.md
    ├── matching_dev.md
    ├── agent_dev.md
    └── crawler_dev.md          # 新增
```

**文档体系说明**：
- **总规划文档**: `.trae/documents/tender_system_implementation_plan.md` - 项目总纲，把控大方向
- **子规划文档**: `docs/plans/*.md` - 各模块详细规划，与总规划保持一致
- **开发记录文档**: `docs/dev-logs/*.md` - 各模块开发过程记录
- **总开发日志**: `memory.md` - 周期性汇总更新

**文档更新流程**：
1. 开发过程严格按照子规划文档执行
2. 每个模块的开发记录实时更新到对应的 `*_dev.md`
3. 周期性汇总更新到 `memory.md`

**更新文件**：
- `.trae/documents/tender_system_implementation_plan.md` - 升级到 v2.1，添加文档体系说明

---

## 待办事项

- [x] 集成测试 ✅
- [x] 文档体系建立 ✅
- [x] 基础功能完整流程 ✅
- [x] 前端界面开发 ✅
- [ ] 部署配置

---

## 2026-04-01

### 基础功能完整流程实施 ✅

**目标**: 完成最基础功能闭环：抓取 → 提取 → 入库 → 匹配 → 推荐

#### Phase 1: 数据层 ✅

**修改文件**：
- `backend/app/models/tender.py` - 扩展 Tender 模型，新增提取结果字段
- `backend/app/models/analysis.py` - 新建 AnalysisResult 分析结果模型
- `backend/app/models/company.py` - 新建 CompanyProfile 公司画像模型
- `backend/app/models/__init__.py` - 更新模型导出
- `backend/app/db/repository.py` - 完善 Repository 方法
- `backend/app/db/session.py` - 添加数据库初始化

**Tender 模型新增字段**：
- budget_amount, budget_confidence - 预算金额和置信度
- deadline - 投标截止时间
- qualifications - 资质要求（JSON）
- contact_person, contact_phone, contact_email - 联系人信息
- tags - 标签（JSON）
- extraction_status, extraction_time - 提取状态

**AnalysisResult 模型**：
- 匹配结果：pass_gate, gate_checks, match_score, match_grade, recommendation
- Agent决策：decision_action, decision_reason, decision_confidence, risks

#### Phase 2: 服务层 ✅

**新建文件**：
- `backend/app/services/pipeline_service.py` - 数据流转主服务

**核心功能**：
- `process_tender()` - 处理单个招标：提取 → 匹配 → 推荐
- `process_batch()` - 批量处理
- `process_unanalyzed()` - 处理未分析的招标
- `get_full_analysis()` - 获取完整分析结果

#### Phase 3: API层 ✅

**修改文件**：
- `backend/app/api/v1/endpoints/tenders.py` - 新增分析端点
- `backend/app/api/v1/endpoints/company.py` - 新建公司配置 API
- `backend/app/api/v1/api.py` - 注册新路由
- `backend/app/main.py` - 更新启动逻辑

**新增 API 端点**：
```
POST /api/tenders/{id}/analyze      # 触发单个分析
POST /api/tenders/analyze-batch     # 批量分析
POST /api/tenders/analyze-unanalyzed # 分析未处理招标
GET  /api/tenders/{id}/analysis     # 获取分析结果
GET  /api/tenders/recommended/list  # 获取推荐列表
GET  /api/company/                  # 获取公司画像
PUT  /api/company/                  # 更新公司画像
```

#### Phase 4: 测试验证 ✅

**新建文件**：
- `backend/tests/test_pipeline_service.py` - PipelineService 集成测试

**测试结果**：
```
======================== 59 passed, 6 warnings in 0.35s ========================
```

---

### 最小 MVP 前端实现 ✅

**目标**: 实现最小化前端界面，让用户能够看到招标列表和分析结果

#### Phase 1: 前端项目搭建 ✅

**新建文件**：
- `frontend/package.json` - 前端依赖配置
- `frontend/vite.config.ts` - Vite 配置（含代理到后端）
- `frontend/tsconfig.json` - TypeScript 配置
- `frontend/index.html` - 入口 HTML
- `frontend/src/main.tsx` - React 入口文件
- `frontend/src/App.tsx` - 主应用组件（含导航栏）
- `frontend/src/services/api.ts` - Axios 基础配置
- `frontend/src/services/tender.ts` - 招标 API 服务
- `frontend/src/services/company.ts` - 公司画像 API 服务
- `frontend/src/types/index.ts` - 通用类型定义
- `frontend/src/types/tender.ts` - 招标相关类型
- `frontend/src/types/company.ts` - 公司画像类型

**技术栈**：Vite + React + TypeScript + Ant Design

#### Phase 2: 招标列表页面 ✅

**新建文件**：`frontend/src/pages/TenderList.tsx`

**功能**：
- 展示招标基本信息（标题、预算、发布日期）
- 匹配评分展示（A/B/C/D 等级，颜色区分）
- 推荐等级标签（强烈推荐/推荐/观望/不推荐）
- 分页功能
- 查看详情按钮

#### Phase 3: 分析详情弹窗 ✅

**新建文件**：`frontend/src/components/AnalysisDetailModal.tsx`

**功能**：
- 提取信息展示（预算、截止日期、资质要求、标签、联系人）
- Gate 检查结果展示（通过/未通过状态）
- Ranking 评分详情（总分、等级、各维度得分）
- Agent 决策建议（行动、置信度、理由、风险点）

#### Phase 4: 公司画像配置页面 ✅

**新建文件**：`frontend/src/pages/CompanyProfile.tsx`

**功能**：
- 公司名称配置
- 目标领域选择（多选）
- 预算范围配置
- 资质证书配置
- 服务区域配置
- 保存和重置功能

#### Phase 5: 测试数据创建 ✅

**新建文件**：`backend/scripts/create_test_data.py`

**测试数据**：5条招标数据 + 1条公司画像数据

#### Phase 6: 问题修复 ✅

**修复内容**：
- 前端 API 响应格式问题
- 缺失依赖安装（sqlmodel, alembic 等）

---

## 已完成任务汇总（最终）

| 任务 | 状态 | 文件数 |
|------|------|--------|
| 目录结构重构 | ✅ | - |
| 多阶段信息抽取 Pipeline | ✅ | 6 |
| Gate + Ranking 双层匹配 | ✅ | 4 |
| Orchestrator 决策 Agent | ✅ | 6 |
| 反馈学习闭环 | ✅ | 2 |
| 轻量级知识图谱 | ✅ | 4 |
| 集成测试 | ✅ | 5 |
| 文档体系建立 | ✅ | 11 |
| 基础功能完整流程 | ✅ | 8 |
| 最小 MVP 前端 | ✅ | 16+ |

**总计新建/修改文件**: 60+ 个文件

---

## 启动说明

```bash
# 后端服务
cd /home/wushuxin/TenderAgent/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端服务
cd /home/wushuxin/TenderAgent/frontend
npm install
npm run dev

# 创建测试数据
cd /home/wushuxin/TenderAgent/backend
python scripts/create_test_data.py
```

**访问地址**：
- 前端：http://localhost:3000
- 后端：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 2026-04-02

### MVP 基线状态校准

**已完成（MVP 功能闭环）**：
- 多阶段信息抽取 Pipeline（粗抽 → 归一化 → 交叉验证）
- Gate + Ranking 双层匹配引擎
- Orchestrator 决策 Agent（含 Qualification/Risk/Competition）
- 反馈学习与轻量知识图谱基础能力
- 基础流程闭环：抓取 → 提取 → 入库 → 匹配 → 推荐
- 最小前端可用页面：招标列表、分析详情、公司画像配置

**当前测试基线**：
- 后端测试：59 passed（含抽取、匹配、Agent、E2E、PipelineService）
- 前端状态：可构建可运行，尚未建立自动化测试脚本链路

**未完成（工程化缺口）**：
- [ ] 部署配置（暂不含 Docker，先完善运行手册与监控告警）
- [x] CI 自动化（后端测试 + 前端构建 + 结构漂移检测）
- [x] 数据层工程化（环境变量驱动数据库连接）
- [x] 前端自动化测试（smoke 级别已打通）

**文档口径统一决议**：
- `memory.md` 作为“当前进度真相”基线
- `README.md` 保持与仓库实际结构、启动方式一致
- `.trae/documents/tender_system_implementation_plan.md` 增加“执行偏差说明”，记录规划与现状差异

### 2026-04-02 - 工程化推进记录（非 Docker）

**本轮已完成**：
- 更新 `README.md`：同步当前 MVP 状态、目录结构、文档索引与启动命令
- 更新 `.trae/documents/tender_system_implementation_plan.md`：新增“v2.1 执行偏差说明”
- 新增 `deploy/README.md`：最小部署说明与环境变量约定
- 新增 `.github/workflows/ci.yml`：后端测试、前端构建、结构漂移检测
- 更新 `backend/app/db/session.py`：支持 `DATABASE_URL` 与 `DB_ECHO` 环境变量
- 更新 `frontend/package.json`：新增 `test` 与 `test:smoke` 脚本
- 新增 `docs/dev-logs/feedback_dev.md` 与 `docs/dev-logs/knowledge_dev.md`
- 新增 `backend/scripts/health_check.py` 作为健康检查脚本样例
- 新增 `scripts/start_mvp.sh` 一键启动脚本（同时启动后端与前端）
- 更新 `scripts/start_mvp.sh`：若 `venv` 不存在则自动创建并安装后端依赖
- 更新 `scripts/start_mvp.sh`：支持 `start|stop|status|restart` 启停与状态查询
- 更新 `scripts/start_mvp.sh`：增加端口占用检测，启动失败时给出端口切换提示，并避免半启动残留
- 更新 `scripts/start_mvp.sh` 与 `frontend/vite.config.ts`：启动时自动切换空闲端口并动态注入前端代理目标，避免“页面获取失败”
- 更新 `AnalysisDetailModal.tsx`：`destroyOnClose` 替换为 `destroyOnHidden`，并在分析结果不存在时自动触发分析后重试获取
- 更新 `frontend/src/services/tender.ts`：前端分页参数转换为后端 `skip/limit`，避免列表请求参数不匹配
- 修复 `frontend/src/services/tender.ts` 与 `frontend/src/services/company.ts`：统一适配 axios 拦截器返回体，消除“获取招标列表失败/获取公司配置失败”
- 修复 `TenderList.tsx` 预算格式化空值崩溃；更新 `frontend/src/services/tender.ts` 将后端字段归一化为前端结构，避免 `toFixed` 读取 `undefined`
- 更新 `frontend/src/services/tender.ts`：将后端 `extraction_status=completed` 映射为前端 `analyzed`，避免列表状态长期显示“待分析”
- 更新 `README.md`：补充一键启动命令入口

**验证结果**：
- `pytest -q`：59 passed

### 2026-04-13 - P1-2 启动：抽取质量对比评估脚本

**新增脚本**：
- `backend/scripts/evaluate_extraction_modes.py`
  - 支持 `rule/agent/both` 三种评估模式
  - 输出字段覆盖率、成功率、平均耗时、错误 TopN
  - 支持 `--agent-timeout`，防止 LLM 超时导致脚本卡住

**当前样本结论（示例）**：
- Rule 模式：抽取稳定、耗时毫秒级
- Agent 模式：当前存在超时情况（示例为 `agent_timeout>8s`），导致成功率偏低

**用途**：
- 作为 Agent 优化阶段的基线工具，用于持续对比 Prompt/模型/网关调整后的质量与性能变化。

### 2026-04-13 - 分析触发策略调整为“仅手动”

**策略变更**：
- 分析改为仅手动触发，不再由抓取链路自动触发。

**改动点**：
- `backend/scripts/run_data_pipeline.py`
  - 移除自动分析流程（不再调用 `process_unanalyzed`）
  - 脚本仅负责“抓取+增量入库”，分析状态输出为 `manual_only`
- `frontend/src/components/AnalysisDetailModal.tsx`
  - 移除 404 场景的自动分析
  - 新增“手动分析”按钮，由用户显式触发
- `README.md`
  - 同步更新数据管道说明，明确“抓取守护不自动分析”

**验证结果**：
- `python backend/scripts/run_data_pipeline.py --help`：参数已移除自动分析选项
- `npm run build`：通过
- `npm run build`：通过
- `npm run test`（smoke）：通过
- `python backend/scripts/health_check.py`：health_check_ok
- `bash -n scripts/start_mvp.sh`：语法检查通过
- 前端代理接口验证：`/api/tenders/` 与 `/api/company/` 均返回 200

### 2026-04-02 - MVP 完成确认

**结论**：
- 当前 MVP 已完成并可稳定演示：招标列表、分析详情、公司配置、自动分析闭环、一键启停
- 前后端关键链路验证通过，端口冲突与代理目标问题已修复

**MVP 验收项**：
- [x] 抓取 → 提取 → 入库 → 匹配 → 推荐闭环可运行
- [x] 招标列表与详情可正常加载，异常项自动触发分析后重试
- [x] 公司配置页面可正常读取与更新
- [x] 一键脚本支持 `start|stop|status|restart`，并支持端口自动切换
- [x] 后端测试、前端构建与 smoke 检查通过

**后续阶段目标（Next）**：
- P1：功能实现优先：API 能力扩展、业务策略增强、前端功能完善
- P2：工程化配套保障：部署配置完善（暂不含 Docker）、迁移流程规范化
- P3：质量深化：前端测试从 smoke 升级到组件/交互级自动化测试

### 2026-04-02 - 数据抓取服务打通（定时 + 增量 + 分析）

**目标**：
- 打通“定时抓取 → 增量入库 → 从数据库取未分析数据并分析”的完整链路

**本轮实现**：
- 更新 `crawlers/main_scraper.py`：
  - 支持按抓取源配置运行（`cmcc`/`telecom`）
  - 支持 `max_pages` 参数化
  - 返回抓取汇总（成功/失败/新增数）
  - 兼容可选爬虫依赖缺失场景
- 更新 `crawlers/scrapers/__init__.py`：
  - 爬虫模块改为可选导入，避免缺失 Playwright 时整体崩溃
- 新增 `backend/scripts/run_data_pipeline.py`：
  - `--mode once`：一次性执行抓取、增量入库与未分析数据处理
  - `--mode daemon --time HH:MM`：按天定时执行
  - 支持 `--scrapers`、`--max-pages`、`--analyze-limit`、`--skip-analysis`
- 更新 `backend/requirements.txt`：补充 `playwright`
- 更新 `README.md`：补充数据抓取服务一次执行与定时执行命令

**验证结果**：
- `python backend/scripts/run_data_pipeline.py --mode once ...` 可正常执行并输出结构化汇总
- 在缺失爬虫依赖时，服务可降级运行并给出安装提示，不会中断分析链路

### 2026-04-13 - 数据抓取链路实跑与运行方式固化

**结论**：
- 已完成真实链路验证：`cmcc + telecom` 抓取成功，新增入库 40 条，未分析数据处理 40 条
- 已固化运行方式：后续统一使用项目虚拟环境解释器执行 `run_data_pipeline.py`
- 暂不落地 `systemd` 服务文件，先保持命令方式运行

**统一命令**：
- `/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode once --scrapers cmcc,telecom --max-pages 1 --analyze-limit 50`
- `/home/wushuxin/TenderAgent/venv/bin/python backend/scripts/run_data_pipeline.py --mode daemon --time 02:00 --scrapers cmcc,telecom --max-pages 2 --analyze-limit 200`

### 2026-04-13 - 功能实现推进（批量分析/失败重试/健康指标）

**后端 API 细化**：
- 更新 `backend/app/api/v1/endpoints/tenders.py`：
  - `POST /api/tenders/analyze-batch` 返回结构细化为 `success/failed/success_ids/failed_items/retryable_ids`
  - 兼容 `tenderIds` 与 `tender_ids` 入参
- 新增 `backend/app/api/v1/endpoints/feedback.py`：
  - `POST /api/feedback/bid` 记录投标反馈
  - `PUT /api/feedback/result/{record_id}` 更新中标结果
  - `GET /api/feedback/stats`、`GET /api/feedback/records` 反馈统计与记录查询
- 更新 `backend/app/api/v1/endpoints/dashboard.py`：
  - 新增 `GET /api/dashboard/crawler-health?hours=24`

**服务与脚本增强**：
- 更新 `backend/app/services/pipeline_service.py`：新增 `process_batch_detailed()`，输出批量处理成功/失败明细
- 更新 `backend/app/db/repository.py`：新增 `get_crawler_health_stats()`，输出近窗成功率、平均耗时、新增数、待分析积压
- 更新 `backend/scripts/health_check.py`：在 `health_check_ok` 后输出 `crawler_health` JSON 指标

**前端交互增强**：
- 更新 `frontend/src/pages/TenderList.tsx`：
  - 新增列表多选
  - 新增“批量分析（已选 N）”
  - 新增“失败重试（N）”
- 更新 `frontend/src/services/tender.ts` 与 `frontend/src/types/tender.ts`：
  - 对齐批量分析返回结构
  - 入参兼容转换与失败可重试 ID 回传

**验证结果**：
- `pytest -q`：59 passed
- `npm run build`：通过
- `python backend/scripts/health_check.py`：输出 `health_check_ok` 与 `crawler_health` 指标 JSON

### 2026-04-13 - 前端反馈录入入口打通

**实现内容**：
- 新增 `frontend/src/services/feedback.ts`，封装：
  - `recordBidFeedback()` -> `POST /api/feedback/bid`
  - `updateBidResult()` -> `PUT /api/feedback/result/{record_id}`
- 更新 `frontend/src/components/AnalysisDetailModal.tsx`：
  - 新增“反馈闭环（投标与结果）”区域
  - 支持录入投标报价并创建反馈记录
  - 支持标记“中标/未中标”，并可填写未中标原因

**验证结果**：
- `npm run build`：通过

### 2026-04-13 - 列表看板与稳定性修复（分页/统计/自适应/外链）

**问题与修复**：
- 修复分页 500：
  - 根因是 Repository 依赖会话未释放导致 SQLAlchemy QueuePool 耗尽
  - 更新 `backend/app/db/repository.py`：`get_repository()` 与 `get_company_repository()` 改为 `yield` 依赖并在 `finally` 关闭会话
- 修复匹配评分与推荐等级不显示：
  - 更新 `backend/app/db/repository.py`：列表查询合并最新分析结果，补齐 `match_score/match_grade/recommendation`
- 优化看板统计口径：
  - 更新 `backend/app/api/v1/endpoints/tenders.py`：`GET /api/tenders/` 增加 `summary`
  - 更新 `backend/app/db/repository.py`：新增 `get_tender_overview()`（全量统计 total/analyzed/pending/strong_recommended）
- 优化前端列表自适应与信息密度：
  - 更新 `frontend/src/pages/TenderList.tsx`：断点响应、列结构压缩、合并日期列、去除强制横向滚动
  - 合并“匹配评分 + 推荐等级 + 状态”为单列“评估结果”徽章展示
- 增加公告外链能力：
  - 更新 `frontend/src/services/tender.ts`、`frontend/src/types/tender.ts` 与 `TenderList.tsx`
  - 标题支持点击跳转 `source_url`（新窗口）

**视觉重构推进**：
- 更新 `frontend/src/App.tsx`：顶部看板风格与统一容器
- 更新 `frontend/src/pages/CompanyProfile.tsx`：分区卡片 + 摘要侧栏
- 更新 `frontend/src/components/AnalysisDetailModal.tsx`：Tabs 分栏展示

**验证结果**：
- `pytest -q`：59 passed
- `npm run build`：通过
- 已完成 git 提交：`8b8cd20`（本地领先 `origin/main` 1 个提交，待 push）

### 2026-04-13 - Agent 分析链路接入与联调完成

**核心目标**：
- 将“规则/正则为主”的抽取链路升级为可配置 Agent 抽取（LiteLLM），并保留规则回退保障稳定性。

**后端能力落地**：
- 新增 `backend/app/services/extraction/agent_extractor.py`（LiteLLM 抽取服务）
- 更新 `backend/app/services/pipeline_service.py`：
  - 支持 `EXTRACTION_MODE=rule|agent|hybrid`
  - `hybrid` 模式优先 Agent，失败回退 Rule
  - 新增 `debug_extraction()` 输出执行模式与回退信息
- 更新 `backend/app/api/v1/endpoints/tenders.py`：
  - 新增 `GET /api/tenders/{id}/analysis-debug`
  - `POST /api/tenders/{id}/analyze?debug=true` 返回 `debug_meta`
- 更新 `backend/app/core/config.py` 与 `.env.example`：
  - 增加 `EXTRACTION_MODE` 配置
  - 固定读取项目根目录 `.env`

**调试与测试脚本**：
- 新增 `backend/scripts/test_agent_extraction.py`（连通性 + pipeline 调试）
- 新增 `backend/scripts/test_llm_connectivity.py`（仅测 LLM 连通）

**问题定位与修复**：
- 初始未走 Agent 的根因：
  - 模型 provider 前缀不规范
  - `LLM_BASE_URL` 使用了 `/chat/completions` 端点路径（需归一化到 `/v1`）
  - 运行进程环境缺少 `litellm` 或依赖版本冲突
- 已修复：模型与 base_url 归一化、超时控制、依赖安装与环境读取路径。

**联调结论**：
- 当前链路可走 Agent，`analysis-debug` 可观测 `selected_mode` 与 `fallback_used`。
- 多实例并存会导致“前端看起来很快但没走 Agent”的错觉；需确保前端代理指向当前后端端口。

### 2026-04-13 - P1-1 落地：fallback 率统计与指标接口

**实现内容**：
- 新增 `backend/app/models/analysis_trace.py`（分析执行轨迹表）
  - 记录字段：`configured_mode`、`selected_mode`、`fallback_used`、`success`、`error_count`、`duration_ms`
- 更新 `backend/app/services/pipeline_service.py`
  - `process_tender()` 落库每次分析轨迹
  - 轨迹包含执行模式与耗时，便于统计 Agent 命中率
- 更新 `backend/app/db/repository.py`
  - 新增 `get_analysis_mode_stats(hours)` 统计
  - 输出 `agent_rate`、`fallback_rate`、`success_rate`、`avg_duration_ms`
- 更新 `backend/app/api/v1/endpoints/dashboard.py`
  - 新增 `GET /api/dashboard/analysis-mode-metrics?hours=24`

**验证结果**：
- `pytest -q`：59 passed
