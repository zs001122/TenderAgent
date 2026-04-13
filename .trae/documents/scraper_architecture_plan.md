# 数据采集层主控制脚本及增量更新架构设计

## 1. 目标与需求
针对现有的和未来的多个招标网站爬虫（如中国电信 `chinatelecom_playwright_scraper.py`、中国移动 `scrape_cmcc_bidding.py`），设计一个统一的主控制脚本（Master Scraper/Orchestrator）。
该架构需要满足以下需求：
1. **统一入口**：通过一个主脚本调度所有子爬虫。
2. **易于扩展**：新增网站爬虫时，只需遵循标准接口，即可即插即用。
3. **数据库直连**：采集的数据不再输出到独立的 CSV，而是直接通过 ORM 或 API 同步到数据库。
4. **增量更新机制**：每天定时运行，爬虫应能识别库中已有数据，实现增量抓取（遇到旧数据自动停止翻页）。

## 2. 架构设计

### 2.1 目录结构调整建议
将现有的爬虫脚本统一放入 `scripts/scrapers/` 目录下，并建立统一的抽象基类。
```text
/home/wushuxin/TenderAgent/scripts/
├── main_scraper.py          # 爬虫主控脚本 (入口点)
├── scrapers/
│   ├── __init__.py          # 导出所有爬虫类
│   ├── base_scraper.py      # 爬虫抽象基类 (定义标准接口)
│   ├── telecom_scraper.py   # 中国电信爬虫 (继承基类)
│   └── cmcc_scraper.py      # 中国移动爬虫 (继承基类)
```

### 2.2 抽象基类设计 (`base_scraper.py`)
定义一个标准化的爬虫接口，所有子爬虫必须实现这些方法：
- `name`: 属性，爬虫标识（如 "中国电信", "中国移动"）。
- `run(max_pages: int, last_publish_date: datetime)`: 核心抓取方法。接收最大页数和该渠道库中最新一条数据的发布时间。
- `parse_list(page)`: 解析列表页。
- `parse_detail(url)`: 解析详情页。

### 2.3 增量更新逻辑
在主控脚本或基类中实现增量判断：
1. **启动前查询**：主脚本启动某渠道爬虫前，从数据库查询该渠道 `source_site` 最近一次成功抓取的记录时间（或者最新的 `publish_date`）。
2. **抓取中判断**：
   - 如果爬取到的某条公告 `publish_date < 库中最新时间`，或者 `source_url` 已在库中存在（通过数据库去重查询），则判定为已抓取过。
   - 如果一页中大部分数据（或连续N条数据）都已存在，爬虫触发 **提前终止（Early Stop）** 信号，停止继续翻页。
3. **数据入库**：抓取到的标准数据字典（符合 `Tender` 模型）通过 `TenderRepository` 直接写入数据库。

### 2.4 主控制脚本 (`main_scraper.py`)
主脚本负责：
1. 初始化数据库连接。
2. 注册所有启用的爬虫实例。
3. 循环遍历每个爬虫：
   - 获取该爬虫对应的增量基准时间。
   - 调用爬虫的 `run()` 方法。
   - 捕获异常，记录爬取日志（写入 `CrawlLog` 表：开始时间、结束时间、新增条数、状态等）。

## 3. 实施步骤

### 步骤 1：创建爬虫基类
- 编写 `base_scraper.py`，定义统一的数据返回格式（匹配数据库的 `Tender` 模型字段）。

### 步骤 2：重构现有爬虫
- **中国电信**：将现有的 `chinatelecom_playwright_scraper.py` 封装为类，继承基类，移除 CSV 写入，改为 `yield` 或返回数据列表。添加基于时间的增量停止逻辑。
- **中国移动**：将 `scrape_cmcc_bidding.py` 同样进行重构封装。

### 步骤 3：编写主控脚本
- 创建 `main_scraper.py`。
- 引入后端的 `app.db.session` 和 `app.models.tender`。
- 实现任务调度和日志记录逻辑。

### 步骤 4：自动化部署 (Cron)
- 编写 shell 脚本，激活虚拟环境并运行 `main_scraper.py`。
- 在 Linux 服务器配置 `crontab -e`，例如每天凌晨 2:00 执行：
  `0 2 * * * /path/to/run_scraper.sh >> /path/to/scraper.log 2>&1`

## 4. 后期扩展指南
当需要新增如“中国联通”爬虫时：
1. 在 `scrapers/` 下新建 `unicom_scraper.py`。
2. 继承 `BaseScraper`，实现特定网站的解析逻辑。
3. 在 `main_scraper.py` 的注册列表中添加 `UnicomScraper()`。
主程序即可自动为其执行增量查询、数据抓取和入库。
