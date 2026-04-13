# 招标商机挖掘系统详细实施计划（优化版）

> **版本**: v2.1  
> **更新日期**: 2026-03-31  
> **状态**: 第一阶段已完成，进入第二阶段

---

## 📚 文档体系说明

本文档为**总规划文档**，把控项目大方向。各模块有对应的**子规划文档**和**开发记录文档**：

| 模块 | 子规划文档 | 开发记录文档 | 状态 |
|------|------------|--------------|------|
| 信息抽取 | [01_extraction_pipeline.md](../../docs/plans/01_extraction_pipeline.md) | [extraction_dev.md](../../docs/dev-logs/extraction_dev.md) | ✅ 已完成 |
| 匹配引擎 | [02_matching_engine.md](../../docs/plans/02_matching_engine.md) | [matching_dev.md](../../docs/dev-logs/matching_dev.md) | ✅ 已完成 |
| Agent系统 | [03_agent_system.md](../../docs/plans/03_agent_system.md) | [agent_dev.md](../../docs/dev-logs/agent_dev.md) | ✅ 已完成 |
| 反馈学习 | [04_feedback_learning.md](../../docs/plans/04_feedback_learning.md) | [feedback_dev.md](../../docs/dev-logs/feedback_dev.md) | ✅ 基础完成 |
| 知识图谱 | [05_knowledge_graph.md](../../docs/plans/05_knowledge_graph.md) | [knowledge_dev.md](../../docs/dev-logs/knowledge_dev.md) | ✅ 基础完成 |
| 数据抓取 | [06_crawler_system.md](../../docs/plans/06_crawler_system.md) | [crawler_dev.md](../../docs/dev-logs/crawler_dev.md) | ⏳ 已有基础 |

**文档更新流程**：
1. 开发过程严格按照子规划文档执行
2. 每个模块的开发记录实时更新到对应的 `*_dev.md`
3. 周期性汇总更新到 `memory.md`

---

## 架构升级说明

### 核心升级点（基于用户反馈）

| 原设计 | 升级后 | 说明 |
|--------|--------|------|
| 单次抽取 | 多阶段抽取 Pipeline | 粗抽 → 归一化 → 交叉验证 |
| 加权评分 | Gate + Ranking 双层结构 | 硬门槛 + 软评分 |
| 多Agent分析 | Orchestrator 决策 Agent | 多Agent分析 → 单Agent决策 |
| 无反馈 | 反馈学习闭环 | 推荐 → 投标 → 中标 → 优化 |
| 重知识图谱 | 轻量级图谱 | 只做资质映射、行业分类、公司关系 |

### 新架构流程图

```
┌──────────────┐
│  数据抓取层   │
└──────┬───────┘
       ↓
┌────────────────────────┐
│ 信息融合层（关键升级） │  ← 不是简单抽取
│  - 粗抽（Recall优先）  │
│  - 归一化              │
│  - 交叉验证            │
└────────┬─────────────┘
         ↓
┌────────────────────────┐
│ Gate过滤层（硬条件）   │  ← 新增
│  - 资质必须满足        │
│  - 地域必须符合        │
│  - 时间必须可参与      │
└────────┬─────────────┘
         ↓
┌────────────────────────┐
│ Ranking评分层          │
│  - 经验匹配            │
│  - 预算匹配            │
│  - 历史中标概率        │
└────────┬─────────────┘
         ↓
┌────────────────────────┐
│ 决策Agent（核心）      │  ← 新增
│  - 是否参与            │
│  - 理由（可解释）      │
│  - 风险点              │
│  - 建议策略            │
└────────┬─────────────┘
         ↓
┌────────────────────────┐
│ 反馈学习系统（闭环）   │  ← 新增
│  - 是否投标            │
│  - 是否中标            │
│  - 输在哪              │
└────────────────────────┘
```

---

## 第零阶段：目录结构重构 ✅ 已完成

**完成时间**: 2026-03-31 14:27

详见 `memory.md`

---

## 第一阶段：核心架构升级 ✅ 已完成

**完成时间**: 2026-03-31 17:00

### 任务 1.1：多阶段信息抽取 Pipeline ✅

**交付物**：
- `backend/app/services/extraction/pipeline.py`
- `backend/app/services/extraction/rough_extractor.py`
- `backend/app/services/extraction/normalizer.py`
- `backend/app/services/extraction/validator.py`
- `backend/app/services/extraction/models.py`

**详细文档**: [01_extraction_pipeline.md](../../docs/plans/01_extraction_pipeline.md)

---

### 任务 1.2：Gate + Ranking 双层匹配算法 ✅

**交付物**：
- `backend/app/services/matching/gate_filter.py`
- `backend/app/services/matching/ranking_engine.py`
- `backend/app/services/matching/matching_engine.py`

**详细文档**: [02_matching_engine.md](../../docs/plans/02_matching_engine.md)

---

### 任务 1.3：Orchestrator 决策 Agent ✅

**交付物**：
- `backend/app/agents/base_agent.py`
- `backend/app/agents/qualification_agent.py`
- `backend/app/agents/risk_agent.py`
- `backend/app/agents/competition_agent.py`
- `backend/app/agents/orchestrator.py`

**详细文档**: [03_agent_system.md](../../docs/plans/03_agent_system.md)

---

### 任务 1.4：反馈学习闭环 ✅

**交付物**：
- `backend/app/models/feedback.py`
- `backend/app/services/feedback_learner.py`

**详细文档**: [04_feedback_learning.md](../../docs/plans/04_feedback_learning.md)

---

### 任务 1.5：轻量级知识图谱 ✅

**交付物**：
- `backend/app/knowledge/qualification_mapping.py`
- `backend/app/knowledge/industry_classification.py`
- `backend/app/knowledge/company_relation.py`

**详细文档**: [05_knowledge_graph.md](../../docs/plans/05_knowledge_graph.md)

---

### 集成测试 ✅

**测试结果**: 51 个测试全部通过

**测试文件**：
- `backend/tests/conftest.py`
- `backend/tests/test_extraction.py`
- `backend/tests/test_matching.py`
- `backend/tests/test_agents.py`
- `backend/tests/test_e2e.py`

---

## v2.1 执行偏差说明（2026-04-02）

### 1) API 路径口径差异
- 规划口径（原）：`/api/v1/extract|match|feedback`
- 当前实现（实际）：`/api/tenders/*`、`/api/company/*`
- 处理策略：后续以“兼容优先”推进，新增分层 API 时保持旧端点可用，避免前端回归风险

### 2) 前端阶段状态差异
- 规划口径（原）：第三阶段“前端界面开发待开始”
- 当前实现（实际）：最小前端 MVP 已完成（列表、分析详情、公司画像）
- 处理策略：第三阶段改为“前端工程化增强”（测试、状态管理、错误处理）

### 3) 当前主线调整
- 从“工程化补齐”调整为“功能实现优先，工程化并行保障”
- 近期优先级：
  1. API 端点功能完善（抽取/匹配/反馈能力）
  2. 业务策略增强（规则、决策、反馈闭环）
  3. 前端功能完善（交互、可视化、批量操作）
  4. 工程化保障（部署、迁移、测试）

---

## 第二阶段：API 端点更新 (待开始)

### 任务 2.1：信息抽取 API
- [ ] POST /api/v1/extract - 单条抽取
- [ ] POST /api/v1/extract/batch - 批量抽取

### 任务 2.2：匹配分析 API
- [ ] POST /api/v1/match - 单条匹配
- [ ] POST /api/v1/match/batch - 批量匹配
- [ ] POST /api/v1/analyze - 综合分析

### 任务 2.3：反馈记录 API
- [ ] POST /api/v1/feedback/bid - 记录投标
- [ ] PUT /api/v1/feedback/result - 更新结果

---

## 第三阶段：前端界面开发 (待开始)

### 任务 3.1：招标列表页
### 任务 3.2：项目详情页
### 任务 3.3：分析结果展示
### 任务 3.4：公司画像配置

---

## 第四阶段：部署配置 (待开始)

### 任务 4.1：Docker 容器化
### 任务 4.2：数据库迁移
### 任务 4.3：定时任务配置
### 任务 4.4：监控告警

---

## 实施优先级

### 🥇 第一优先级（已完成）
1. ✅ 目录结构重构
2. ✅ 多阶段信息抽取 Pipeline
3. ✅ Gate + Ranking 双层匹配
4. ✅ Orchestrator 决策 Agent
5. ✅ 集成测试

### 🥈 第二优先级（进行中）
1. ⏳ API 端点更新
2. ⏳ 前端界面开发
3. ⏳ 反馈学习增强

### 🥉 第三优先级（后期）
1. ⏳ 部署配置
2. ⏳ 性能优化
3. ⏳ 监控告警

---

## 预期成果

完成本计划后，系统将具备以下能力：
- **信息提取稳定性**：多阶段 Pipeline，支持交叉验证 ✅
- **匹配可解释性**：Gate + Ranking 双层结构，决策理由清晰 ✅
- **决策智能化**：Orchestrator Agent 统一决策 ✅
- **持续优化能力**：反馈学习闭环，越用越聪明 ✅
- **轻量知识支持**：资质映射、行业分类、公司关系 ✅
