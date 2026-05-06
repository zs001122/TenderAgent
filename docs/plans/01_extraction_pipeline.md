# 信息抽取模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 01  
> **优先级**: 🥇 最高  
> **状态**: ✅ 已完成核心功能

---

## 1. 模块概述

### 1.1 目标
从招标公告（正文+附件）中稳定、准确地提取关键信息，解决招标文件格式不统一、信息分散的问题。

### 1.2 核心挑战
- 预算可能写成："约500万元"、"￥5,000,000"、"详见附件"
- 资质要求可能在正文、评分表、附件扫描件
- 截止时间格式多样
- 联系人信息可能不完整

### 1.3 解决方案
采用**多阶段抽取 Pipeline**：
```
粗抽（Recall优先）→ 归一化（标准化）→ 交叉验证（一致性检查）
```

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                  InformationFusionPipeline              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │RoughExtractor│→│FieldNormalizer│→│ConsistencyValidator│ │
│  │  (粗抽)     │  │  (归一化)   │  │  (验证)     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 组件详细设计

### 3.1 RoughExtractor（粗抽模块）
**职责**: 从文本中提取所有可能的信息，Recall优先，允许脏数据

**提取字段**:
| 字段 | 提取方式 | 支持格式 |
|------|----------|----------|
| 预算 | 正则表达式 | 万元/元/亿元/￥/人民币 |
| 截止时间 | 正则表达式 | YYYY年MM月DD日/YYYY-MM-DD |
| 资质要求 | 关键词匹配 | 资质要求/投标人须具备 |
| 联系人 | 正则表达式 | 联系人/电话/邮箱 |
| 地区 | 关键词匹配 | 项目地点/实施地点 |
| 项目类型 | 关键词匹配 | 招标/询比/竞争性谈判 |

**文件**: `backend/app/services/extraction/rough_extractor.py`

### 3.2 FieldNormalizer（归一化模块）
**职责**: 标准化字段格式，解决同一概念不同表述的问题

**归一化规则**:
| 字段 | 原始值 | 归一化值 |
|------|--------|----------|
| 资质 | CMMI三级 | CMMI3 |
| 资质 | 信息安全管理体系认证 | ISO27001 |
| 预算 | 5,000,000元 | 500万元 |
| 地区 | 广东省深圳市 | 广东省 |

**文件**: `backend/app/services/extraction/normalizer.py`

### 3.3 ConsistencyValidator（交叉验证模块）
**职责**: 检查数据一致性，标记可疑数据

**验证规则**:
- 正文预算 vs 附件预算是否一致
- 截止时间是否合理（未过期）
- 必填字段是否完整

**文件**: `backend/app/services/extraction/validator.py`

---

## 4. 数据模型

```python
@dataclass
class BudgetInfo:
    value: Optional[float]      # 预算值（万元）
    unit: str                   # 单位
    confidence: float           # 置信度
    raw_values: List[Dict]      # 原始提取值
    source: str                 # 来源

@dataclass
class ExtractedInfo:
    budget: BudgetInfo
    deadline: DeadlineInfo
    qualifications: QualificationInfo
    contact: ContactInfo
    tags: List[str]
    region: str
    project_type: str
    is_reliable: bool
```

**文件**: `backend/app/services/extraction/models.py`

---

## 5. 接口设计

### 5.1 主接口
```python
class InformationFusionPipeline:
    def extract(self, content: str, attachments: List[str] = None) -> ExtractionResult:
        """执行完整的信息提取流程"""
        pass
    
    def quick_extract(self, content: str) -> dict:
        """快速提取 - 仅返回关键字段"""
        pass
    
    def extract_batch(self, items: List[dict]) -> List[ExtractionResult]:
        """批量提取"""
        pass
```

### 5.2 返回结构
```python
@dataclass
class ExtractionResult:
    success: bool
    info: ExtractedInfo
    errors: List[str]
    warnings: List[str]
```

---

## 6. 测试要求

### 6.1 单元测试
- [x] 预算提取测试（万元/元/亿元格式）
- [x] 日期提取测试（多种格式）
- [x] 资质提取测试
- [x] 联系人提取测试
- [x] 关键词提取测试

### 6.2 集成测试
- [x] Pipeline 完整流程测试
- [x] 批量处理测试
- [x] 空内容处理测试

**测试文件**: `backend/tests/test_extraction.py`

---

## 7. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| 数据模型设计 | ✅ | 2026-03-31 |
| RoughExtractor 实现 | ✅ | 2026-03-31 |
| FieldNormalizer 实现 | ✅ | 2026-03-31 |
| ConsistencyValidator 实现 | ✅ | 2026-03-31 |
| Pipeline 集成 | ✅ | 2026-03-31 |
| 单元测试 | ✅ | 2026-03-31 |
| 集成测试 | ✅ | 2026-03-31 |

---

## 8. 后续优化方向

- [ ] LLM 增强提取（处理复杂表述）
- [ ] 附件 PDF 解析增强
- [ ] OCR 图片识别
- [ ] 表格数据提取
- [ ] 历史数据学习优化

---

## 9. 相关文档

- **开发记录**: [extraction_dev.md](../dev-logs/extraction_dev.md)
- **API 文档**: 待创建
- **测试报告**: 已集成到测试框架
