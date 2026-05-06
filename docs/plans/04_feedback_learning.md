# 反馈学习模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 04  
> **优先级**: 🥈 高  
> **状态**: ✅ 已完成基础功能

---

## 1. 模块概述

### 1.1 目标
建立投标结果反馈闭环，持续优化匹配和决策模型。

### 1.2 核心流程
```
投标记录 → 结果跟踪 → 偏差分析 → 模型优化
```

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   FeedbackLearner                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ record_bid  │→│record_result│→│   optimize  │     │
│  │ (记录投标)  │  │ (记录结果)  │  │ (优化模型)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

```python
class BidRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tender_id: str
    tender_title: str
    predicted_action: str
    predicted_confidence: float
    actual_result: Optional[str]
    won: Optional[bool]
    actual_budget: Optional[float]
    created_at: datetime
    updated_at: datetime

class FeedbackAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bid_record_id: int
    prediction_correct: bool
    deviation_analysis: str
    optimization_suggestions: str
    created_at: datetime
```

**文件**: `backend/app/models/feedback.py`

---

## 4. 接口设计

```python
class FeedbackLearner:
    def __init__(self, db_session: Session):
        pass
    
    def record_bid(self, tender_info: Dict, company_profile: Dict, 
                   predicted_action: str, confidence: float) -> int:
        """记录投标决策"""
        pass
    
    def record_result(self, bid_id: int, won: bool, actual_budget: float = None) -> None:
        """记录投标结果"""
        pass
    
    def analyze_prediction_accuracy(self) -> Dict:
        """分析预测准确性"""
        pass
    
    def get_optimization_suggestions(self) -> List[Dict]:
        """获取优化建议"""
        pass
```

**文件**: `backend/app/services/feedback_learner.py`

---

## 5. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| 数据模型设计 | ✅ | 2026-03-31 |
| FeedbackLearner 实现 | ✅ | 2026-03-31 |
| 基础测试 | ✅ | 2026-03-31 |

---

## 6. 后续优化方向

- [ ] 自动化结果跟踪
- [ ] 模型参数自动调优
- [ ] A/B 测试框架
- [ ] 可视化分析面板

---

## 7. 相关文档

- **开发记录**: [feedback_dev.md](../dev-logs/feedback_dev.md)
