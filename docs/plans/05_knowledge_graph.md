# 知识图谱模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 05  
> **优先级**: 🥈 高  
> **状态**: ✅ 已完成基础功能

---

## 1. 模块概述

### 1.1 目标
构建轻量级知识图谱，支持资质映射、行业分类、公司关系分析。

### 1.2 核心功能
- 资质等效性映射
- 行业分类体系
- 公司关系网络

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Knowledge Layer                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │Qualification│  │  Industry   │  │  Company    │     │
│  │  Mapping    │  │Classification│ │  Relation   │     │
│  │ (资质映射)  │  │ (行业分类)  │  │ (公司关系)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 组件详细设计

### 3.1 QualificationMapping（资质映射）
**职责**: 处理资质名称的标准化和等效性判断

**映射规则**:
```python
EQUIVALENT_QUALIFICATIONS = {
    'CMMI3': ['CMMI三级', 'CMMI 3级', 'CMMI-3'],
    'ISO27001': ['信息安全管理体系认证', 'ISO 27001', '信息安全认证'],
    '高新技术企业': ['高新企业', '国家高新技术企业'],
}
```

**文件**: `backend/app/knowledge/qualification_mapping.py`

### 3.2 IndustryClassification（行业分类）
**职责**: 基于关键词的行业分类

**分类体系**:
```python
INDUSTRY_TREE = {
    '软件开发': {
        'keywords': ['软件开发', '系统开发', '应用开发'],
        'subcategories': ['Web开发', '移动开发', '桌面应用']
    },
    '大数据': {
        'keywords': ['大数据', '数据平台', '数据分析'],
        'subcategories': ['数据治理', '数据可视化', '数据挖掘']
    },
}
```

**文件**: `backend/app/knowledge/industry_classification.py`

### 3.3 CompanyRelationGraph（公司关系图）
**职责**: 分析公司间的竞争关系

**功能**:
- 竞争对手识别
- 中标率分析
- 关系网络构建

**文件**: `backend/app/knowledge/company_relation.py`

---

## 4. 接口设计

```python
class QualificationMapping:
    @staticmethod
    def normalize(qualification: str) -> str:
        """标准化资质名称"""
        pass
    
    @staticmethod
    def are_equivalent(qual1: str, qual2: str) -> bool:
        """判断两个资质是否等效"""
        pass

class IndustryClassification:
    @staticmethod
    def classify_keywords(keywords: List[str]) -> Dict:
        """基于关键词分类"""
        pass

class CompanyRelationGraph:
    def get_competitors(self, company_name: str) -> List[str]:
        """获取竞争对手"""
        pass
    
    def get_win_rate(self, company_name: str) -> float:
        """获取中标率"""
        pass
```

---

## 5. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| QualificationMapping 实现 | ✅ | 2026-03-31 |
| IndustryClassification 实现 | ✅ | 2026-03-31 |
| CompanyRelationGraph 实现 | ✅ | 2026-03-31 |
| 基础测试 | ✅ | 2026-03-31 |

---

## 6. 后续优化方向

- [ ] 知识图谱可视化
- [ ] 自动化知识抽取
- [ ] 图数据库集成（Neo4j）
- [ ] 知识推理能力

---

## 7. 相关文档

- **开发记录**: [knowledge_dev.md](../dev-logs/knowledge_dev.md)
