# 智能分析层 (AI Analysis Layer) Demo 实施计划

## 目标
构建一个智能分析层的演示版本 (Demo)，展示如何从招标公告中提取关键信息、评估商机匹配度，并输出分析报告。

## 步骤

### 1. 准备测试数据 (Data Preparation)
由于实际抓取的 CSV 数据可能不够完整或缺乏结构化信息，我们将创建一个包含丰富示例数据的模拟文件 (`mock_tenders.json`)，用于演示分析功能。
- **数据内容**: 包含 3-5 个典型的招标公告样本（软件开发、硬件采购、服务外包等）。
- **字段**: 标题、正文内容（包含预算、截止时间、资质要求等隐含信息）、发布时间。

### 2. 构建分析器核心 (Analyzer Core)
创建 `tender_analysis_demo.py`，实现以下功能模块：

#### 2.1 基础信息提取 (Rule-based Extraction)
- **预算提取 (`extract_budget`)**: 使用正则表达式识别 "XX万元"、"XX亿" 等金额描述。
- **时间提取 (`extract_deadline`)**: 识别 "截止时间"、"开标时间" 等日期格式。
- **关键词匹配 (`extract_keywords`)**: 基于预定义的行业关键词库（如 "大数据"、"AI"、"云计算"）进行标签化。

#### 2.2 模拟 LLM 智能分析 (Mock LLM Analysis)
- **`LLMAnalyzer` 类**: 模拟调用大模型 API 的接口。
- **Prompt 构建**: 展示如何构建用于提取结构化数据（JSON）的 Prompt。
- **模拟响应**: 返回预设的结构化分析结果（如风险评估、竞争对手推测），展示 AI 分析的潜力。

#### 2.3 商机匹配引擎 (Matching Engine)
- **公司画像定义**: 定义一个简单的公司画像（资质、核心技术、目标预算区间）。
- **打分逻辑 (`calculate_match_score`)**:
    - 关键词匹配度 (40%)
    - 预算匹配度 (30%)
    - 资质符合度 (30%)
- **推荐建议**: 根据分数生成 "强烈推荐"、"一般推荐" 或 "不推荐"。

### 3. 输出分析报告 (Reporting)
- 将分析结果汇总，生成 `analysis_report.md` 或 JSON 文件。
- 在终端打印高亮的关键信息摘要。

## 交付物
- `mock_tenders.json`: 测试数据
- `tender_analysis_demo.py`: 分析脚本
- `analysis_results.json`: 分析结果
