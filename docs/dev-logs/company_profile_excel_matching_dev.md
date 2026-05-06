# 公司资料 Excel 导入与精准匹配改造进度

> **开发主题**: 公司资料结构化、Excel 导入、Gate + Ranking 精准匹配  
> **关联功能**: 公司画像、资料库、招标分析、匹配评估  
> **当前状态**: 三阶段已完成并通过测试、构建和隔离库 API 冒烟验证
> **记录日期**: 2026-04-29
> **最近更新**: 2026-05-06

---

## 1. 背景与目标

当前系统原有公司画像偏轻量，主要依赖手工维护的公司名称、目标领域、预算范围、资质列表和服务区域。这个结构可以支撑 MVP 演示，但无法充分利用公司真实资料，也无法对招标要求给出有证据链的匹配解释。

本轮改造围绕以下目标展开：

- 支持导入当前目录下的 `智算公司资质（202502）.xlsx`。
- 沿用现有多 Sheet 公司资料结构，不强行简化成单表。
- 将资质、软著、专利、人员、业绩等内容沉淀为结构化资料。
- 匹配评估从简单字符串匹配升级为“硬门槛 + 资料证据评分”。
- 前端公司画像页面升级为资料管理工作台，提供导入预览、资料库维护、匹配策略和校验问题视图。

---

## 2. 已完成改造

### 2.1 公司资料结构化存储

新增 `CompanyAsset` 结构化资料模型，用于统一承载从 Excel 导入的公司证据资料。

覆盖的资料类型包括：

- 企业资质、管理体系、双软证书、荣誉证书、其他认证证书
- 软著
- 已授权专利
- 审核中专利
- 人员证书
- 业绩合同

每条资料保留基础证据字段：

- 资料类型、来源 Sheet、名称、分类
- 证书编号、发证机构、发证日期、有效期、状态
- 合同金额，统一换算为万元
- 关键词、原始行数据、导入批次

关键文件：

- `backend/app/models/company.py`
- `backend/app/models/__init__.py`
- `backend/app/db/session.py`
- `backend/app/db/repository.py`

### 2.2 Excel 导入与校验

新增 `CompanyExcelImporter`，用于解析当前公司资料工作簿。

已支持的 Sheet：

1. 公司基本信息
2. 软著
3. 专利已授权
4. 专利审核中
5. 专业资质认证
6. 管理体系
7. 双软证书
8. 荣誉证书
9. 其他认证证书
10. 人员
11. 业绩

导入时会生成：

- 公司名称
- 导入批次 ID
- 结构化资料列表
- 资料类型统计
- Sheet 维度统计
- 有效资质数量
- 过期资料数量
- 180 天内临期资料数量
- 重复资料与日期解析等校验提示

关键文件：

- `backend/app/services/company_excel_importer.py`
- `backend/requirements.txt`，新增 `openpyxl>=3.1.0`
- `backend/tests/test_company_excel_importer.py`

### 2.3 公司资料 API

新增公司资料导入与查询接口。

接口清单：

- `POST /api/company/import-excel/preview`
  - 上传 `.xlsx` 公司资料文件。
  - 只解析并返回 `preview_id`、导入摘要、校验提示和样例资料，不写入资料库。

- `POST /api/company/import-excel`
  - 接收 `preview_id`。
  - 确认后替换当前结构化资料库。
  - 同步公司名称、有效资质和可推导目标领域到公司画像。
  - 返回导入摘要和校验提示。

- `GET /api/company/assets`
  - 查询结构化资料列表。
  - 返回分页对象。
  - 支持按 `asset_type`、`status`、`source_sheet`、`keyword` 过滤。
  - 支持 `include_deleted=true` 查看已停用资料。

- `GET /api/company/assets/summary`
  - 查询资料库摘要。

- `POST /api/company/assets`
  - 手动新增资料。

- `PUT /api/company/assets/{asset_id}`
  - 编辑已有资料，导入资料被编辑后标记为 `manual_edit`。

- `DELETE /api/company/assets/{asset_id}`
  - 软删除/停用资料。

- `POST /api/company/assets/{asset_id}/restore`
  - 恢复已停用资料。

同时，`GET /api/company/` 已扩展返回：

- `asset_summary`
- `assets`

关键文件：

- `backend/app/api/v1/endpoints/company.py`
- `backend/app/db/repository.py`
- `frontend/src/services/company.ts`
- `frontend/src/types/company.ts`

### 2.4 匹配引擎升级

原有匹配引擎仍保留 Gate + Ranking 两层结构。本轮在不破坏原有 `qualifications` 手工列表的前提下，增加了结构化资料参与匹配。

Gate 层变化：

- 资质门槛继续作为强制项。
- 公司手工资质和 Excel 导入的有效资质共同参与资质命中。
- 只使用状态为 `有效` 的导入资质。
- 增强 CMMI 等级类资质识别，例如 `CMMI-Level 5` 可匹配 `CMMI5`。

Ranking 层变化：

- 新增 `资料证据` 评分维度。
- 根据招标标题、标签、正文、资质要求等关键词，匹配导入的业绩、软著、专利、人员证书和资质。
- 输出命中的资料证据，例如来源 Sheet 和资料名称。
- 权重调整为：
  - 经验匹配 25%
  - 预算匹配 20%
  - 历史中标 20%
  - 竞争程度 15%
  - 资料证据 20%

Agent 层变化：

- `QualificationAgent` 也会读取 Excel 导入的有效资质，避免 Agent 判断和 Gate 判断不一致。

关键文件：

- `backend/app/services/matching/gate_filter.py`
- `backend/app/services/matching/ranking_engine.py`
- `backend/app/agents/qualification_agent.py`
- `backend/tests/test_matching.py`

### 2.5 前端公司画像页面

公司画像配置页已重构为资料管理工作台。

已完成能力：

- 上传并预览 `.xlsx` 公司资料文件。
- 确认后入库，避免上传即覆盖。
- 展示结构化资料总数、有效资质数、过期/临期数量、资料类型统计和服务区域。
- `资料库` Tab 支持分页、资料类型/状态/来源 Sheet/关键词筛选。
- 支持新增、编辑、停用、恢复资料。
- 支持资料详情抽屉查看原始 JSON、来源类型和停用原因。
- `匹配策略` Tab 继续维护公司画像配置。
- `校验问题` Tab 展示导入警告和资料状态统计。

关键文件：

- `frontend/src/pages/CompanyProfile.tsx`
- `frontend/src/services/company.ts`
- `frontend/src/types/company.ts`

---

## 3. 当前实现范围

当前已完成“资料导入 + 资料库维护 + 证据化匹配 + 分析详情展示”的闭环。

已覆盖：

- 当前 `智算公司资质（202502）.xlsx` 的多 Sheet 解析。
- 导入前预览与人工确认。
- 公司资料结构化入库。
- 公司资料分页、筛选、摘要展示。
- 手动新增、编辑、软删除和恢复资料。
- 有效资质参与 Gate。
- 业绩、软著、专利、人员证书等资料参与 Ranking 加分。
- `matching_details` 持久化 Gate 证据、资料证据、缺失项、风险项和维度评分。
- 分析详情页展示匹配证据 Tab。
- 导入校验提示。
- 后端单元测试、前端构建和隔离库 API 冒烟验证。

暂未覆盖：

- Excel 模板下载。
- 导入历史版本管理与回滚。
- 招标附件解析。
- 更细的人员数量门槛，例如“项目经理 1 人 + 安全工程师 2 人”。
- 更细的业绩门槛，例如“近三年同类项目不少于 3 个且单项金额大于 500 万”。
- 正式 Alembic 迁移脚本，当前仍使用 `create_all` 加 SQLite 轻量兼容补列。

---

## 4. 验证结果

### 4.1 后端测试

已执行：

```powershell
venv\Scripts\python -m pytest backend\tests
```

结果：

```text
64 passed
```

覆盖内容：

- 公司资料 Excel 解析测试
- 公司资料导入预览/确认相关回归覆盖
- 公司资料手动新增、编辑、软删除、恢复测试
- Gate + Ranking 匹配测试
- 结构化资料证据匹配测试
- 空资质/空资料字段回归测试
- Agent 测试
- 抽取测试
- E2E 测试
- PipelineService 回归测试

### 4.2 前端构建

已执行：

```powershell
npm run build
```

结果：

```text
✓ built
```

说明：

- Vite 构建通过。
- 仍存在 chunk 体积提示，属于既有前端体积问题，不影响本轮功能正确性。

### 4.3 本地服务验证

曾启动并验证：

- Backend: `http://localhost:8012`
- Frontend: `http://localhost:3012`
- `GET /api/company/assets/summary` 返回 200。
- 前端首页返回 200。

说明：

- 原脚本启动时遇到旧 pid/端口状态不一致，因此使用明确端口单独启动验证。
- Windows/Vite 曾出现 `spawn EPERM`，通过非沙箱启动前端服务验证通过。

2026-05-06 追加隔离库 API 冒烟：

- 使用 `.runtime` 临时 SQLite 库，不污染默认业务库。
- 覆盖 `POST /api/company/import-excel/preview`。
- 覆盖 `POST /api/company/import-excel`。
- 覆盖资料新增、编辑、停用、恢复。
- 覆盖 `POST /api/tenders/analyze-batch`。
- 结果：`api_smoke_ok`。

---

## 5. 后续待办

### P0：导入体验与资料可信度

- 增加导入历史批次，支持查看上次导入时间、导入文件名、导入人和导入结果。
- 增加导入回滚，避免误上传覆盖当前可用资料库。
- 增加模板说明或模板下载，明确每个 Sheet 的必填字段、日期格式和状态枚举。

### P1：匹配精准度

- 将人员要求从普通关键词匹配升级为数量/类别门槛。
- 将业绩要求升级为时间、金额、行业、客户类型、项目关键词的组合匹配。
- 给每个 Gate 失败项增加可操作建议，例如“缺少 CCRC，可联合体/外协/放弃”。

### P2：抓取信息处理

- 对招标公告增加更细的结构化字段：
  - 人员要求
  - 业绩要求
  - 认证要求
  - 附件要求
  - 评分办法关键词
- 增加公告附件解析，优先覆盖 PDF、Word、Excel 附件。
- 保存抽取字段对应原文片段，提升匹配解释可信度。

### P3：工程化

- 为 `CompanyAsset` 增加正式 Alembic 迁移。
- 增加导入 API 的 TestClient 自动化测试。
- 优化前端 bundle 体积。
- 统一旧文档与新文档目录，减少 `.trae/documents`、`docs/plans`、`docs/dev-logs` 之间的信息重复。

---

## 6. 当前结论

本轮改造已经把公司资料从“手工标签配置”推进到“Excel 多 Sheet 结构化资料库”，并让这些资料进入匹配评估链路。

现在系统已经具备以下基础能力：

- 能导入当前公司资质 Excel。
- 能识别有效/过期/临期资料。
- 能把有效资质用于硬门槛判断。
- 能把业绩、软著、专利、人员证书用于资料证据评分。
- 能在前端工作台展示导入预览、资料库维护、匹配策略和校验问题。
- 能在分析详情页展示匹配证据链。

下一阶段重点不应再继续堆更多简单字段，而应增强“要求抽取”和“证据解释”：从招标公告中抽出人员、业绩、资质、金额、年限等明确要求，再用公司资料库逐条对照，输出可复核的命中/缺失证据。

---

## 7. 第二阶段：资料管理工作台与证据化匹配

> **状态**: 已完成  
> **完成日期**: 2026-04-29

### 7.1 前端资料管理工作台

原 `公司画像配置` 页面已重构为 `资料管理工作台`。

主要变化：

- 页面从单一表单改为工作台结构。
- 顶部展示资料库概览：结构化资料、有效资质、过期资料、临期资料、资料类型、服务区域。
- 使用 Tabs 分区：
  - `资料导入`
  - `资料库`
  - `匹配策略`
  - `校验问题`
- `资料库` 支持按资料类型、状态、来源 Sheet、关键词筛选。
- 资料表格支持分页和详情抽屉。
- `匹配策略` 继续维护公司名称、目标领域、预算范围、补充资质、服务区域。

关键文件：

- `frontend/src/pages/CompanyProfile.tsx`
- `frontend/src/types/company.ts`
- `frontend/src/services/company.ts`

### 7.2 Excel 导入流程改造

导入流程从“上传即覆盖”改为“预览确认后入库”。

新增流程：

1. 上传 Excel。
2. 后端解析并返回预览结果。
3. 前端展示资料数量、有效资质、过期数量、校验提示和样例资料。
4. 用户确认后，后端才替换当前资料库并同步公司画像。

新增/调整接口：

- `POST /api/company/import-excel/preview`
  - 只解析，不写库。
  - 返回 `preview_id`、导入摘要、校验提示、样例资料。
- `POST /api/company/import-excel`
  - 接收 `preview_id`。
  - 确认写入资料库。
- `GET /api/company/assets`
  - 返回分页对象。
  - 支持 `asset_type`、`status`、`source_sheet`、`keyword`、`skip`、`limit`。
- `GET /api/company/assets/summary`
  - 增加 `by_status` 状态统计。

关键文件：

- `backend/app/api/v1/endpoints/company.py`
- `backend/app/db/repository.py`

### 7.3 匹配引擎证据化输出

匹配引擎已从“只给分/字符串原因”升级为结构化证据链输出。

新增输出结构：

- `matching_details.dimension_scores`
  - 各评分维度的名称、分数、权重、解释。
- `matching_details.gate_evidence`
  - Gate 层硬门槛证据。
- `matching_details.evidence_matches`
  - Ranking 层资料证据命中。
- `matching_details.missing_items`
  - 缺失项。
- `matching_details.risk_items`
  - 弱命中或需人工复核项。

证据项字段：

- `dimension`
- `requirement`
- `status`
- `score_delta`
- `matched_assets`
- `reason`
- `is_mandatory`

关键文件：

- `backend/app/services/matching/matching_engine.py`
- `backend/app/services/matching/ranking_engine.py`
- `backend/app/services/pipeline_service.py`
- `backend/app/models/analysis.py`

### 7.4 分析详情页展示证据链

分析详情弹窗新增 `匹配证据` Tab。

已展示：

- 命中数量
- 缺失数量
- 风险/复核数量
- Gate 硬门槛证据
- 资料证据命中
- 命中的公司资料来源 Sheet 和资料名称

评分详情页也补充展示各维度分数、权重和说明。

关键文件：

- `frontend/src/components/AnalysisDetailModal.tsx`
- `frontend/src/types/tender.ts`

### 7.5 数据兼容

新增 `AnalysisResult.matching_details` 字段。

兼容处理：

- 新分析会写入结构化匹配详情。
- 旧分析没有 `matching_details` 时，前端降级显示原有 Gate 和总分。
- SQLite 旧库通过启动时轻量兼容逻辑补充 `matching_details` 列。

关键文件：

- `backend/app/models/analysis.py`
- `backend/app/db/session.py`

### 7.6 验证结果

后端测试：

```powershell
venv\Scripts\python -m pytest backend\tests
```

结果：

```text
64 passed
```

前端构建：

```powershell
npm run build
```

结果：

```text
✓ built
```

说明：

- Vite 仍提示 chunk 超过 500 kB，属于既有前端体积问题。
- 本阶段未引入向量库或额外 LLM 调用，匹配仍以规则和资料证据解释为主。

---

## 8. 第三阶段：资料库手动维护

> **状态**: 已完成  
> **完成日期**: 2026-04-29

### 8.1 手动维护能力

资料库已从“只读导入结果”升级为可人工维护。

已支持：

- 手动新增资料。
- 编辑已有资料。
- 软删除/停用资料。
- 恢复已停用资料。
- 列表筛选时可选择是否显示已停用资料。

手动维护字段覆盖：

- 资料类型
- 来源
- 资料名称
- 分类
- 证书/合同编号
- 发证机构/客户
- 发证/签订日期
- 有效期至/结束日期
- 状态
- 金额
- 关键词
- 原始数据 JSON

### 8.2 后端改造

新增字段：

- `CompanyAsset.source_type`
- `CompanyAsset.is_deleted`
- `CompanyAsset.deleted_at`
- `CompanyAsset.deleted_reason`

新增接口：

- `POST /api/company/assets`
- `PUT /api/company/assets/{asset_id}`
- `DELETE /api/company/assets/{asset_id}`
- `POST /api/company/assets/{asset_id}/restore`

行为约定：

- 删除采用软删除，不物理删除。
- 默认资料列表、统计和匹配排除 `is_deleted=true` 的资料。
- `include_deleted=true` 时可以查看已停用资料。
- 手动新增资料标记为 `manual`。
- Excel 导入资料被编辑后标记为 `manual_edit`。

关键文件：

- `backend/app/models/company.py`
- `backend/app/api/v1/endpoints/company.py`
- `backend/app/db/repository.py`
- `backend/app/db/session.py`

### 8.3 前端改造

资料库 Tab 新增：

- `新增资料` 按钮。
- 编辑资料 Drawer。
- 停用资料操作。
- 恢复资料操作。
- `显示已停用` 开关。
- 详情抽屉展示来源类型、停用状态和停用原因。

编辑表单采用通用结构，适配资质、软著、专利、人员证书和业绩等资料类型。

关键文件：

- `frontend/src/pages/CompanyProfile.tsx`
- `frontend/src/services/company.ts`
- `frontend/src/types/company.ts`

### 8.4 匹配兼容

匹配引擎已排除停用资料。

- Gate 资质命中排除 `is_deleted=true` 的资质。
- Ranking 资料证据评分排除 `is_deleted=true` 的资料。
- QualificationAgent 排除停用资质。
- 证据引用中保留 `source_type`，可区分 Excel 导入、手工新增、手工编辑。

关键文件：

- `backend/app/services/matching/gate_filter.py`
- `backend/app/services/matching/ranking_engine.py`
- `backend/app/agents/qualification_agent.py`

### 8.5 验证结果

新增测试：

- `backend/tests/test_company_assets.py`

覆盖：

- 新增资料。
- 编辑资料。
- 软删除资料。
- 默认查询排除停用资料。
- `include_deleted=true` 查询停用资料。
- 恢复资料。

后端测试：

```powershell
venv\Scripts\python -m pytest backend\tests
```

结果：

```text
64 passed
```

前端构建：

```powershell
npm run build
```

结果：

```text
✓ built
```
