# 数据抓取模块子规划

> **总规划引用**: [招标商机挖掘系统详细实施计划](../../.trae/documents/tender_system_implementation_plan.md)  
> **模块编号**: 06  
> **优先级**: 🥈 高  
> **状态**: ⏳ 已有基础实现，待增强

---

## 1. 模块概述

### 1.1 目标
从多个招标网站自动抓取招标公告数据，支持增量抓取、去重、错误恢复。

### 1.2 核心挑战
- 不同网站结构差异大
- 反爬机制（验证码、IP限制）
- 动态渲染页面（JavaScript）
- 数据格式不统一

### 1.3 解决方案
采用**插件化爬虫架构**：
```
BaseScraper（抽象基类）→ 多个具体爬虫实现 → 统一数据输出
```

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    MainScraper                          │
│                   (爬虫调度中心)                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ChinaMobile  │  │ChinaTelecom │  │   Other     │     │
│  │  Scraper    │  │  Scraper    │  │  Scrapers   │     │
│  │ (中国移动)  │  │ (中国电信)  │  │  (其他)     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   数据处理层                            │
│  - 去重检查                                             │
│  - 数据清洗                                             │
│  - 入库存储                                             │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 组件详细设计

### 3.1 BaseScraper（爬虫基类）
**职责**: 定义爬虫的通用接口和行为

**核心接口**:
```python
class BaseScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """爬虫名称"""
        pass
    
    @abstractmethod
    def run(self, max_pages: int = 3, last_publish_date: datetime = None) -> Iterator[Dict]:
        """执行爬虫，yield 招标数据"""
        pass
```

**文件**: `crawlers/scrapers/base_scraper.py`

### 3.2 已实现的爬虫

| 爬虫 | 目标网站 | 实现方式 | 状态 |
|------|----------|----------|------|
| ChinaMobileScraper | 中国移动招标网 | requests | ✅ 可用 |
| ChinaTelecomScraper | 中国电信招标网 | Playwright | ✅ 可用 |
| APIScraper | API接口 | requests | ✅ 可用 |

**文件**: `crawlers/scrapers/`

### 3.3 MainScraper（调度中心）
**职责**: 协调多个爬虫，管理抓取任务

**功能**:
- 爬虫注册与调度
- 增量抓取（基于最后发布日期）
- 去重检查
- 错误处理与日志记录
- 抓取统计

**文件**: `crawlers/main_scraper.py`

---

## 4. 数据模型

### 4.1 招标数据结构
```python
{
    "source_url": str,           # 来源URL
    "source_site": str,          # 来源网站
    "title": str,                # 标题
    "publish_date": datetime,    # 发布日期
    "notice_type": str,          # 公告类型
    "content": str,              # 正文内容
    "region": str,               # 地区
    "budget": float,             # 预算（可选）
    "deadline": datetime,        # 截止时间（可选）
}
```

### 4.2 抓取日志
```python
class CrawlLog(SQLModel, table=True):
    id: Optional[int]
    source_site: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str  # RUNNING/SUCCESS/FAILED
    new_count: int
    error_message: Optional[str]
```

---

## 5. 接口设计

### 5.1 命令行接口
```bash
# 运行所有爬虫
python -m crawlers.main_scraper

# 运行指定爬虫
python -m crawlers.main_scraper --scraper cmcc

# 指定页数
python -m crawlers.main_scraper --max-pages 5
```

### 5.2 编程接口
```python
from crawlers.main_scraper import run_scrapers

# 运行所有爬虫
run_scrapers()

# 单独使用爬虫
from crawlers.scrapers import ChinaMobileScraper
scraper = ChinaMobileScraper()
for tender in scraper.run(max_pages=3):
    print(tender['title'])
```

---

## 6. 待增强功能

### 6.1 短期优化
- [ ] 添加更多数据源（中国联通、政府采购网等）
- [ ] 代理IP池支持
- [ ] 验证码识别
- [ ] 抓取频率控制

### 6.2 中期优化
- [ ] 分布式抓取
- [ ] 实时监控面板
- [ ] 自动错误恢复
- [ ] 数据质量检查

### 6.3 长期优化
- [ ] 智能反爬策略
- [ ] 自动化网站适配
- [ ] 大规模分布式架构

---

## 7. 开发进度

| 任务 | 状态 | 完成日期 |
|------|------|----------|
| BaseScraper 基类 | ✅ | 已有 |
| ChinaMobileScraper | ✅ | 已有 |
| ChinaTelecomScraper | ✅ | 已有 |
| MainScraper 调度 | ✅ | 已有 |
| 增量抓取 | ✅ | 已有 |
| 去重检查 | ✅ | 已有 |
| 更多数据源 | ⏳ | 待开发 |
| 代理IP池 | ⏳ | 待开发 |

---

## 8. 相关文档

- **开发记录**: [crawler_dev.md](../dev-logs/crawler_dev.md)
- **爬虫架构设计**: [scraper_architecture_plan.md](../../.trae/documents/scraper_architecture_plan.md)
