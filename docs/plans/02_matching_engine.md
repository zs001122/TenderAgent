# 匹配引擎模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 02  
> **优先级**: 🥇 最高  
> **状态**: ✅ 已完成核心功能，并完成公司资料证据化升级

---

## 1. 模块概述

### 1.1 目标
实现招标项目与公司画像、结构化公司资料库的智能匹配，输出可解释、可复核的推荐决策。

### 1.2 核心挑战
- 硬性条件（资质）不满足时，软评分再高也无意义
- 需要平衡多维度评分
- 决策结果需要可解释
- 公司资料来自 Excel 多 Sheet 和手动维护，必须保留证据来源与停用状态
- 历史分析结果需要持久化匹配证据，避免详情页和当时的匹配结果脱节

### 1.3 解决方案
采用**Gate + Ranking 双层结构**，并在输出中持久化 `matching_details`：
```
Gate过滤（硬门槛）→ Ranking评分（软评分 + 资料证据）→ Decision决策 → matching_details
```

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    MatchingEngine                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ GateFilter  │→│RankingEngine│→│  Decision   │     │
│  │ (硬门槛)    │  │ (软评分)    │  │  (决策)     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 组件详细设计

### 3.1 GateFilter（硬性过滤层）
**职责**: 检查必须满足的硬性条件

**检查项**:
| 检查项 | 类型 | 说明 |
|--------|------|------|
| 资质门槛 | 强制 | 必须具备要求的资质；手工资质和有效 `CompanyAsset` 资质共同参与 |
| 地域门槛 | 非强制 | 是否在服务区域内 |
| 时间门槛 | 强制 | 是否在投标有效期内 |
| 预算门槛 | 非强制 | 是否在预算范围内 |

**结果类型**:
- `PASS`: 通过
- `FAIL`: 不通过（强制项失败则整体失败）
- `WARNING`: 警告（非强制项不满足）

**文件**: `backend/app/services/matching/gate_filter.py`

**当前实现补充**:
- 资质匹配支持从 `company_profile.qualifications` 和 `company_profile.assets` 读取。
- `asset_type=qualification`、状态为 `有效`、且未软删除的资料可参与 Gate。
- CMMI 等级类资质支持等价判断，例如 `CMMI-Level 5` 可匹配 `CMMI5`。

### 3.2 RankingEngine（软评分层）
**职责**: 对通过 Gate 的项目进行多维度评分

**评分维度**:
| 维度 | 权重 | 评分依据 |
|------|------|----------|
| 经验匹配 | 25% | 历史项目相似度 |
| 预算匹配 | 20% | 预算范围契合度 |
| 历史中标 | 20% | 类似项目中标率 |
| 竞争程度 | 15% | 竞争对手分析 |
| 资料证据 | 20% | 业绩、软著、专利、人员证书、资质等结构化公司资料命中 |

**评分等级**:
- A: 80-100分（强烈推荐）
- B: 60-79分（推荐）
- C: 40-59分（观望）
- D: 0-39分（不推荐）

**文件**: `backend/app/services/matching/ranking_engine.py`

**当前实现补充**:
- `RankingResult.evidence_matches` 输出资料证据命中列表。
- `RankingEngine._score_evidence()` 排除 `is_deleted=true` 的资料。
- 资料字段允许存在空值；证据文本拼接会过滤 `None` 和空字符串，避免脏数据打断分析。
- 资料证据引用保留 `id`、`name`、`asset_type`、`source_sheet`、`status`、`certificate_no`、`expiry_date`、`source_type`。

### 3.3 MatchingEngine（匹配引擎）
**职责**: 协调 Gate 和 Ranking，输出最终决策

**决策流程**:
1. 执行 Gate 检查
2. 若 Gate 失败，直接返回"不推荐"
3. 若 Gate 通过，执行 Ranking 评分
4. 综合输出决策结果
5. 构建 `matching_details`，包含 Gate 证据、资料命中、缺失项、风险项和维度评分

**文件**: `backend/app/services/matching/matching_engine.py`

---

## 4. 数据模型

```python
@dataclass
class GateCheck:
    name: str              # 检查项名称
    result: GateResult     # 检查结果
    reason: str            # 原因说明
    is_mandatory: bool     # 是否强制

@dataclass
class RankingResult:
    total_score: float
    grade: str
    dimension_scores: Dict[str, DimensionScore]
    confidence: float
    evidence_matches: List[Dict[str, Any]]

@dataclass
class MatchResult:
    pass_gate: bool
    gate_checks: List[Dict]
    ranking: Optional[RankingResult]
    recommendation: str
    reason: str
    score: float
    grade: str
    details: Dict[str, Any]  # 包含 matching_details
```

`matching_details` 当前结构：

```python
{
    "dimension_scores": {...},
    "gate_evidence": [...],
    "evidence_matches": [...],
    "missing_items": [...],
    "risk_items": [...],
}
```

---

## 5. 接口设计

```python
class MatchingEngine:
    def __init__(self, company_profile: Dict[str, Any], weights: Dict[str, float] = None):
        pass
    
    def match(self, tender_info: Dict[str, Any]) -> MatchResult:
        """执行单个匹配"""
        pass
    
    def match_batch(self, tenders: List[Dict]) -> List[MatchResult]:
        """批量匹配"""
        pass
    
    def get_top_matches(self, tenders: List[Dict], top_n: int = 10) -> List[Dict]:
        """获取 Top N 匹配结果"""
        pass
    
    def filter_by_recommendation(self, tenders: List[Dict], recommendations: List[str]) -> List[Dict]:
        """按推荐级别筛选"""
        pass
```

---

## 6. 测试要求

### 6.1 单元测试
- [x] Gate 资质检查测试
- [x] Gate 地域检查测试
- [x] Gate 时间检查测试
- [x] Gate 预算检查测试
- [x] Ranking 评分测试
- [x] 资料证据评分测试
- [x] 导入资料空字段回归测试

### 6.2 集成测试
- [x] 完整匹配流程测试
- [x] Gate 失败场景测试
- [x] 批量匹配测试
- [x] Top N 筛选测试
- [x] Excel 导入资质参与 Gate 测试
- [x] 资料证据进入 `matching_details` 测试

**测试文件**: `backend/tests/test_matching.py`

---

## 7. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| GateFilter 实现 | ✅ | 2026-03-31 |
| RankingEngine 实现 | ✅ | 2026-03-31 |
| MatchingEngine 集成 | ✅ | 2026-03-31 |
| 单元测试 | ✅ | 2026-03-31 |
| 集成测试 | ✅ | 2026-03-31 |
| 资料证据评分维度 | ✅ | 2026-04-29 |
| `matching_details` 证据链持久化 | ✅ | 2026-04-29 |
| 软删除资料排除匹配 | ✅ | 2026-04-29 |
| 空资料字段回归修复 | ✅ | 2026-05-06 |

---

## 8. 后续优化方向

- [ ] 动态权重调整（基于反馈学习）
- [ ] 竞争对手实时分析
- [ ] 中标概率预测模型
- [ ] 人员要求数量/类别门槛
- [ ] 业绩要求时间、金额、行业、客户类型组合匹配
- [ ] Gate 失败项生成可操作建议

---

## 9. 相关文档

- **开发记录**: [matching_dev.md](../dev-logs/matching_dev.md)
- **API 文档**: 待创建
