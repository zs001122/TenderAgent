# 基础功能完整流程实施计划

> **目标**: 完成最基础功能闭环：抓取 → 提取 → 入库 → 匹配 → 推荐  
> **版本**: v1.0  
> **创建日期**: 2026-04-01

---

## 1. 现状分析

### 1.1 已完成模块
| 模块 | 状态 | 说明 |
|------|------|------|
| 数据抓取 | ✅ 可用 | 中国移动、中国电信爬虫已实现 |
| 信息提取 | ✅ 可用 | Pipeline 已实现，测试通过 |
| 匹配引擎 | ✅ 可用 | Gate + Ranking 双层结构 |
| Agent决策 | ✅ 可用 | Orchestrator 已实现 |
| 集成测试 | ✅ 可用 | 51个测试通过 |

### 1.2 关键断点（需要修复）

```
抓取 ──✅──▶ 入库 ──❌──▶ 提取 ──❌──▶ 匹配 ──❌──▶ 推荐
      │         │         │         │         │
      │         │         │         │         └── Agent决策无API
      │         │         │         └── MatchResult未持久化
      │         │         └── ExtractedInfo未存DB
      │         └── Tender模型字段不完整
      └── 爬虫已可入库
```

### 1.3 主要问题
1. **Tender 模型字段不完整**：缺少 deadline、qualifications、tags 等提取结果字段
2. **ExtractedInfo 未持久化**：提取结果未存入数据库
3. **MatchResult 未持久化**：匹配结果未存入数据库
4. **数据流转断层**：各模块独立，缺少连接代码
5. **API 端点缺失**：匹配和推荐结果无对外 API

---

## 2. 实施任务

### 任务 1：扩展数据模型 🥇 最高优先级

**目标**: 扩展 Tender 模型，新增 AnalysisResult 模型

**修改文件**:
- `backend/app/models/tender.py` - 扩展字段
- `backend/app/models/analysis.py` - 新建分析结果模型

**Tender 模型新增字段**:
```python
class Tender(SQLModel, table=True):
    # 现有字段...
    
    # 提取结果字段
    budget_amount: Optional[float]      # 预算金额（万元）
    budget_confidence: Optional[float]  # 预算置信度
    deadline: Optional[datetime]        # 投标截止时间
    qualifications: Optional[str]       # 资质要求（JSON）
    contact_person: Optional[str]       # 联系人
    contact_phone: Optional[str]        # 联系电话
    contact_email: Optional[str]        # 联系邮箱
    tags: Optional[str]                 # 标签（JSON）
    project_type: Optional[str]         # 项目类型
    extraction_status: Optional[str]    # 提取状态
    extraction_time: Optional[datetime] # 提取时间
```

**AnalysisResult 新模型**:
```python
class AnalysisResult(SQLModel, table=True):
    id: Optional[int]
    tender_id: int                      # 关联招标ID
    
    # 匹配结果
    pass_gate: bool                     # 是否通过门槛
    gate_checks: Optional[str]          # 门槛检查详情（JSON）
    match_score: float                  # 匹配得分
    match_grade: str                    # 匹配等级
    recommendation: str                 # 推荐意见
    
    # Agent决策
    decision_action: str                # 决策：投标/不投标/评估后决定
    decision_reason: Optional[str]      # 决策理由
    decision_confidence: float          # 决策置信度
    risks: Optional[str]                # 风险列表（JSON）
    
    # 元数据
    created_at: datetime
    updated_at: datetime
```

---

### 任务 2：实现数据流转服务 🥇 最高优先级

**目标**: 创建统一的数据流转服务，打通各模块

**新建文件**:
- `backend/app/services/pipeline_service.py` - 主流程服务

**核心逻辑**:
```python
class PipelineService:
    """数据流转主服务"""
    
    def __init__(self, db: Session, company_profile: Dict):
        self.db = db
        self.company_profile = company_profile
        self.extraction_pipeline = InformationFusionPipeline()
        self.matching_engine = MatchingEngine(company_profile)
        self.orchestrator = OrchestratorAgent()
    
    def process_tender(self, tender_id: int) -> AnalysisResult:
        """处理单个招标：提取 → 匹配 → 推荐"""
        # 1. 获取招标数据
        tender = self.db.get(Tender, tender_id)
        
        # 2. 信息提取
        extraction_result = self.extraction_pipeline.extract(tender.content)
        
        # 3. 更新 Tender 提取结果
        self._update_tender_extraction(tender, extraction_result)
        
        # 4. 匹配分析
        tender_info = self._to_match_input(tender, extraction_result)
        match_result = self.matching_engine.match(tender_info)
        
        # 5. Agent 决策
        orchestrator_result = self.orchestrator.analyze(tender_info, self.company_profile)
        
        # 6. 保存分析结果
        analysis = self._save_analysis(tender_id, match_result, orchestrator_result)
        
        return analysis
    
    def process_batch(self, tender_ids: List[int]) -> List[AnalysisResult]:
        """批量处理"""
        return [self.process_tender(tid) for tid in tender_ids]
    
    def process_unanalyzed(self, limit: int = 100) -> int:
        """处理未分析的招标"""
        pass
```

---

### 任务 3：实现 Repository 方法 🥈 高优先级

**目标**: 完善 Repository 层的数据访问方法

**修改文件**:
- `backend/app/db/repository.py`

**新增方法**:
```python
class TenderRepository:
    def get_unanalyzed_tenders(self, limit: int) -> List[Tender]:
        """获取未分析的招标"""
        pass
    
    def update_extraction_result(self, tender_id: int, extraction: ExtractedInfo) -> None:
        """更新提取结果"""
        pass
    
    def save_analysis_result(self, result: AnalysisResult) -> AnalysisResult:
        """保存分析结果"""
        pass
    
    def get_analysis_by_tender_id(self, tender_id: int) -> Optional[AnalysisResult]:
        """根据招标ID获取分析结果"""
        pass
```

---

### 任务 4：新增 API 端点 🥈 高优先级

**目标**: 暴露匹配和推荐结果 API

**修改文件**:
- `backend/app/api/v1/api.py` - 注册路由
- `backend/app/api/v1/endpoints/tenders.py` - 扩展端点

**新增端点**:
```
POST /api/v1/tenders/{id}/analyze      # 触发单个分析
POST /api/v1/tenders/analyze-batch     # 批量分析
GET  /api/v1/tenders/{id}/analysis     # 获取分析结果
GET  /api/v1/tenders/recommended       # 获取推荐列表
```

**API 响应格式**:
```json
{
    "tender_id": 123,
    "title": "某市大数据平台建设项目",
    "extraction": {
        "budget": {"value": 580, "unit": "万元", "confidence": 0.9},
        "deadline": "2026-04-15",
        "qualifications": ["CMMI3", "ISO27001"],
        "tags": ["大数据", "AI"]
    },
    "matching": {
        "pass_gate": true,
        "score": 85,
        "grade": "A",
        "recommendation": "强烈推荐"
    },
    "decision": {
        "action": "投标",
        "confidence": 0.85,
        "reason": "资质完全匹配，预算在范围内",
        "risks": ["时间较紧"]
    }
}
```

---

### 任务 5：公司画像配置 🥉 中优先级

**目标**: 实现公司画像的配置管理

**新建文件**:
- `backend/app/models/company.py` - 公司画像模型
- `backend/app/api/v1/endpoints/company.py` - 公司配置 API

**CompanyProfile 模型**:
```python
class CompanyProfile(SQLModel, table=True):
    id: Optional[int]
    name: str                           # 公司名称
    target_domains: Optional[str]       # 目标领域（JSON）
    budget_range_min: Optional[float]   # 预算范围下限
    budget_range_max: Optional[float]   # 预算范围上限
    qualifications: Optional[str]       # 具备资质（JSON）
    service_regions: Optional[str]      # 服务区域（JSON）
    is_active: bool = True              # 是否启用
```

---

### 任务 6：整合测试 🥉 中优先级

**目标**: 编写完整流程的集成测试

**新建文件**:
- `backend/tests/test_pipeline_service.py`

---

## 3. 实施顺序

```
Phase 1: 数据层 (任务1 + 任务3)
├── 扩展 Tender 模型
├── 新建 AnalysisResult 模型
└── 完善 Repository 方法

Phase 2: 服务层 (任务2)
├── 创建 PipelineService
└── 实现数据流转逻辑

Phase 3: API层 (任务4 + 任务5)
├── 新增分析 API
├── 新增推荐 API
└── 公司画像 API

Phase 4: 测试验证 (任务6)
├── 集成测试
└── 端到端测试
```

---

## 4. 预期成果

完成后可实现：

```bash
# 1. 运行爬虫抓取数据
python -m crawlers.main_scraper

# 2. 触发分析（通过API）
POST /api/v1/tenders/analyze-batch

# 3. 获取推荐列表
GET /api/v1/tenders/recommended

# 4. 查看单个分析结果
GET /api/v1/tenders/{id}/analysis
```

**完整数据流**:
```
爬虫抓取 → Tender表 → PipelineService处理 → AnalysisResult表 → API返回
```

---

## 5. 文件清单

### 新建文件
| 文件 | 说明 |
|------|------|
| `backend/app/models/analysis.py` | 分析结果模型 |
| `backend/app/models/company.py` | 公司画像模型 |
| `backend/app/services/pipeline_service.py` | 数据流转服务 |
| `backend/app/api/v1/endpoints/company.py` | 公司配置 API |
| `backend/tests/test_pipeline_service.py` | 集成测试 |

### 修改文件
| 文件 | 修改内容 |
|------|----------|
| `backend/app/models/tender.py` | 扩展提取结果字段 |
| `backend/app/db/repository.py` | 新增数据访问方法 |
| `backend/app/api/v1/api.py` | 注册新路由 |
| `backend/app/api/v1/endpoints/tenders.py` | 新增分析端点 |

---

## 6. 时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| Phase 1 | 数据层 | 1小时 |
| Phase 2 | 服务层 | 1小时 |
| Phase 3 | API层 | 1小时 |
| Phase 4 | 测试验证 | 0.5小时 |
| **总计** | | **3.5小时** |
