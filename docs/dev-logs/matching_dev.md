# 匹配引擎模块开发记录

> **子规划文档**: [02_matching_engine.md](../plans/02_matching_engine.md)  
> **开发周期**: 2026-03-31 ~ 进行中
> **最近更新**: 2026-05-06

---

## 开发日志

### 2026-03-31

#### 14:30 - GateFilter 实现
- 实现资质门槛检查
- 实现地域门槛检查
- 实现时间门槛检查
- 实现预算门槛检查

**关键代码**:
```python
class GateFilter:
    def check(self, tender_info: Dict) -> List[GateCheck]:
        checks = []
        checks.append(self._check_qualification(tender_info))
        checks.append(self._check_region(tender_info))
        checks.append(self._check_deadline(tender_info))
        checks.append(self._check_budget(tender_info))
        return checks
```

#### 15:00 - RankingEngine 实现
- 实现多维度评分
- 实现权重配置
- 实现评分等级划分

#### 15:30 - MatchingEngine 集成
- 实现 Gate → Ranking → Decision 流程
- 实现批量匹配接口
- 实现 Top N 筛选

#### 16:30 - 测试完成
- 编写单元测试 13 个
- **测试结果**: 全部通过 ✅

---

## 技术决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 双层结构 | Gate + Ranking | 硬软条件分离 |
| 评分权重 | 可配置 | 灵活调整 |
| 决策输出 | 四级推荐 | 清晰明确 |
| 公司资料证据 | Ranking 新增 `资料证据` 维度 | 让 Excel/手工维护资料参与评分，并保留来源 |
| 证据持久化 | `AnalysisResult.matching_details` | 历史分析详情可复核当时的 Gate、命中、缺失和风险 |
| 资料停用 | 匹配层排除 `is_deleted=true` | 软删除资料不再影响 Gate、Ranking 和 Agent 判断 |

---

### 2026-04-29

#### 公司资料证据化匹配升级
- Gate 层继续保留资质、地域、时间、预算检查。
- 资质 Gate 支持同时读取公司画像手工资质和 `CompanyAsset` 中的有效资质。
- CMMI 等级类资质支持更宽松的等价判断，例如 `CMMI-Level 5` 对 `CMMI5`。
- Ranking 新增 `资料证据` 维度，当前权重为 20%。
- Ranking 会根据招标标题、正文、标签、资质要求等关键词命中业绩、软著、专利、人员证书和资质资料。
- 输出 `evidence_matches`，包含证据维度、命中要求、资料引用、分数增量和解释。

#### 结构化证据链
- `MatchingEngine` 输出 `matching_details`。
- `matching_details` 包含：
  - `dimension_scores`
  - `gate_evidence`
  - `evidence_matches`
  - `missing_items`
  - `risk_items`
- `PipelineService` 将 `matching_details` 写入 `AnalysisResult`，历史分析记录可直接展示当时证据。

#### 停用资料兼容
- Gate、Ranking 和 `QualificationAgent` 均排除 `is_deleted=true` 的资料。
- 证据引用保留 `source_type`，用于区分 `excel_import`、`manual` 和 `manual_edit`。

### 2026-05-06

#### 回归修复
- 批量匹配测试中硬编码截止日期已改为动态未来日期，避免测试随时间自然过期。
- `QualificationAgent` 过滤空资质名称，避免导入资料中存在空值时 `join()` 失败。
- `RankingEngine._asset_text()` 过滤 `None` 和空字符串，避免资料证据评分被脏字段打断。

#### 验证
- 后端测试：`64 passed`。
- 隔离库 API 冒烟通过，覆盖 Excel 预览确认、资料 CRUD、软删除/恢复和批量分析。

---

## 性能指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 单次匹配耗时 | ~10ms | <5ms |
| 批量匹配(100条) | ~1s | <500ms |
| 后端匹配相关测试 | 已纳入 `64 passed` 基线 | 持续全绿 |

---

## 下一步计划

1. 动态权重调整
2. 人员要求数量/类别门槛
3. 业绩要求时间、金额、行业、客户类型组合匹配
4. Gate 失败项生成可操作建议
5. 竞争对手实时分析
6. 中标概率预测模型
