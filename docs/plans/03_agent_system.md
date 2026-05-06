# Agent 系统模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 03  
> **优先级**: 🥇 最高  
> **状态**: ✅ 已完成核心功能

---

## 1. 模块概述

### 1.1 目标
构建多 Agent 协作的智能决策系统，实现招标项目的综合分析和决策建议。

### 1.2 核心挑战
- 单一模型难以处理多维度分析
- 不同分析维度需要不同的专业知识
- 需要统一的决策输出

### 1.3 解决方案
采用**Orchestrator 模式**：
```
多个专业Agent → Orchestrator协调 → 统一决策输出
```

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   OrchestratorAgent                     │
│                    (决策编排中心)                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │Qualification│  │   RiskAgent │  │Competition  │     │
│  │   Agent     │  │             │  │   Agent     │     │
│  │ (资质分析)  │  │ (风险评估)  │  │ (竞争分析)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Agent 详细设计

### 3.1 BaseAgent（基类）
**职责**: 定义 Agent 的通用接口和行为

**核心方法**:
```python
class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def analyze(self, tender_info: Dict, company_profile: Dict) -> AgentResult:
        pass
```

**文件**: `backend/app/agents/base_agent.py`

### 3.2 QualificationAgent（资质分析 Agent）
**职责**: 分析资质匹配情况

**分析内容**:
- 已具备资质 vs 要求资质
- 缺失资质识别
- 资质获取难度评估
- 资质等效性判断

**输出**:
```python
{
    'pass': bool,           # 是否通过资质门槛
    'matched': List[str],   # 已匹配资质
    'missing': List[str],   # 缺失资质
    'equivalent': List[str] # 等效资质
}
```

**文件**: `backend/app/agents/qualification_agent.py`

### 3.3 RiskAgent（风险评估 Agent）
**职责**: 评估投标风险

**风险维度**:
| 风险类型 | 评估依据 |
|----------|----------|
| 时间风险 | 截止时间紧迫度 |
| 预算风险 | 预算合理性 |
| 技术风险 | 技术要求匹配度 |
| 竞争风险 | 竞争激烈程度 |

**文件**: `backend/app/agents/risk_agent.py`

### 3.4 CompetitionAgent（竞争分析 Agent）
**职责**: 分析竞争态势，预测中标概率

**分析内容**:
- 历史中标率
- 竞争对手分析
- 中标概率预测

**文件**: `backend/app/agents/competition_agent.py`

### 3.5 OrchestratorAgent（决策编排 Agent）
**职责**: 协调各 Agent，输出最终决策

**决策流程**:
1. 调用所有注册的 Agent 进行分析
2. 收集各 Agent 的分析结果
3. 综合评估，生成决策
4. 输出可解释的决策报告

**决策类型**:
- `投标`: 强烈建议投标
- `评估后决定`: 需要进一步评估
- `不投标`: 不建议投标

**文件**: `backend/app/agents/orchestrator.py`

---

## 4. 数据模型

```python
@dataclass
class AgentResult:
    agent_name: str
    analysis: Dict[str, Any]
    confidence: float
    key_findings: List[str]
    risks: List[str]
    recommendations: List[str]

@dataclass
class DecisionResult:
    action: str              # 投标/不投标/评估后决定
    reason: str              # 决策原因
    confidence: float        # 置信度

@dataclass
class OrchestratorResult:
    decision: DecisionResult
    agent_results: Dict[str, AgentResult]
    summary: str
    confidence: float
```

---

## 5. 接口设计

```python
class OrchestratorAgent:
    def __init__(self, agents: List[BaseAgent] = None):
        pass
    
    def register_agent(self, agent: BaseAgent) -> None:
        """注册 Agent"""
        pass
    
    def analyze(self, tender_info: Dict, company_profile: Dict) -> OrchestratorResult:
        """执行综合分析"""
        pass
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """获取指定 Agent"""
        pass
```

---

## 6. 测试要求

### 6.1 单元测试
- [x] QualificationAgent 测试
- [x] RiskAgent 测试
- [x] CompetitionAgent 测试
- [x] OrchestratorAgent 测试

### 6.2 集成测试
- [x] 多 Agent 协作测试
- [x] 决策流程测试
- [x] 边界条件测试

**测试文件**: `backend/tests/test_agents.py`

---

## 7. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| BaseAgent 实现 | ✅ | 2026-03-31 |
| QualificationAgent 实现 | ✅ | 2026-03-31 |
| RiskAgent 实现 | ✅ | 2026-03-31 |
| CompetitionAgent 实现 | ✅ | 2026-03-31 |
| OrchestratorAgent 实现 | ✅ | 2026-03-31 |
| 单元测试 | ✅ | 2026-03-31 |
| 集成测试 | ✅ | 2026-03-31 |

---

## 8. 后续优化方向

- [ ] LLM 增强 Agent（更智能的分析）
- [ ] 更多专业 Agent（财务分析、技术评估等）
- [ ] Agent 权重动态调整
- [ ] Agent 学习优化

---

## 9. 相关文档

- **开发记录**: [agent_dev.md](../dev-logs/agent_dev.md)
- **API 文档**: 待创建
