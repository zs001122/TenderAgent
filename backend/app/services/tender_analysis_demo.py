import json
import re
import datetime
import pandas as pd
from typing import Dict, List, Any
from openai import OpenAI

# ==========================================
# 1. 基础信息提取层 (Rule-based Extraction)
# ==========================================
class TenderInfoExtractor:
    def __init__(self):
        # 预定义的关键词库
        self.keywords_map = {
            "大数据": ["大数据", "数据清洗", "Hadoop", "Spark", "数据仓库"],
            "AI/人工智能": ["AI", "人工智能", "机器学习", "NLP", "图像识别", "大模型"],
            "软件开发": ["软件开发", "系统建设", "APP", "小程序", "平台开发"],
            "硬件/设备": ["服务器", "电脑", "硬件", "存储", "网络设备"],
            "工程/施工": ["装修", "施工", "改造", "土建", "安装工程"],
            "通信/网络": ["通信", "基站", "光缆", "宽带", "5G", "网络优化"],
            "运维/服务": ["运维", "维护", "驻场", "巡检"]
        }

    def clean_title(self, raw_title: str) -> str:
        """
        清洗标题中的 HYPERLINK 公式
        例如: =HYPERLINK("url", "title") -> title
        """
        if not raw_title:
            return ""
        # 尝试匹配 Excel 公式中的标题部分
        match = re.search(r'HYPERLINK\(".*?",\s*"(.*?)"\)', raw_title)
        if match:
            return match.group(1)
        # 如果不是公式，直接返回
        return raw_title

    def extract_budget(self, content: str) -> float:
        """
        提取预算金额（统一转换为万元）
        支持格式：500万元, 2.5亿, 150000元
        """
        # 匹配 "X万元"
        match_wan = re.search(r'(\d+(\.\d+)?)\s*万元', content)
        if match_wan:
            return float(match_wan.group(1))
        
        # 匹配 "X亿"
        match_yi = re.search(r'(\d+(\.\d+)?)\s*亿', content)
        if match_yi:
            return float(match_yi.group(1)) * 10000
            
        # 匹配 "X元"
        match_yuan = re.search(r'(\d+(,\d{3})*(\.\d+)?)\s*元', content)
        if match_yuan:
            amount_str = match_yuan.group(1).replace(',', '')
            return float(amount_str) / 10000.0
            
        return 0.0

    def extract_deadline(self, content: str) -> str:
        """
        提取截止日期
        """
        # 简单匹配 YYYY-MM-DD
        match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if match:
            return match.group(1)
        return "未知"

    def extract_keywords(self, content: str) -> List[str]:
        """
        提取行业关键词标签
        """
        tags = set()
        for category, keywords in self.keywords_map.items():
            for kw in keywords:
                if kw in content:
                    tags.add(category)
                    break # 该类别匹配到一个即可
        return list(tags)

# ==========================================
# 2. 模拟 LLM 智能分析层 (Real LLM Analysis)
# ==========================================
class LLMAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_with_llm(self, tender_text: str) -> Dict[str, Any]:
        """
        调用 LLM API 进行深度分析
        """
        print(f"DEBUG: 正在调用 LLM ({self.model}) 分析文本 (长度: {len(tender_text)})...")
        
        system_prompt = """
        你是一个专业的招标商机分析专家。请分析给定的招标公告内容，并返回JSON格式的分析结果。
        
        需要提取和分析的字段如下：
        1. risk_assessment: 风险评估（简要原因）
        2. competitor_analysis: 竞争对手分析（简要列举）
        3. technical_difficulty: 技术难度（简要说明）
        4. summary: 简要总结（一句话建议）
        
        请严格按照以下JSON格式返回，不要包含Markdown代码块，保持简练：
        {
            "risk_assessment": "...",
            "competitor_analysis": "...",
            "technical_difficulty": "...",
            "summary": "..."
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                     {"role": "system", "content": system_prompt},
                     {"role": "user", "content": f"招标公告内容：\n{tender_text}"}
                 ],
                 temperature=0.3,
                 max_tokens=4096
             )
            
            content = response.choices[0].message.content
            # print(f"DEBUG: LLM Response Content: {content}")
            
            # 清理 <think> 标签
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            
            # 清理可能的Markdown标记
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尝试提取JSON块
                match = re.search(r'(\{.*\})', content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        pass
                # 打印错误内容以便调试
                print(f"DEBUG: JSON解析失败，原始内容: {content[:200]}...")
                raise
            
        except Exception as e:
            print(f"LLM调用失败: {e}")
            # 降级处理：返回默认空值
            return {
                "risk_assessment": "分析失败",
                "competitor_analysis": "未知",
                "technical_difficulty": "未知",
                "summary": f"API调用出错: {str(e)[:50]}..."
            }


# ==========================================
# 3. 商机匹配引擎 (Matching Engine)
# ==========================================
class MatchingEngine:
    def __init__(self, company_profile: Dict):
        self.company = company_profile

    def calculate_score(self, tender_info: Dict) -> Dict:
        """
        计算匹配得分
        """
        score = 0
        reasons = []

        # 1. 关键词/业务匹配 (40分)
        matched_keywords = [tag for tag in tender_info['tags'] if tag in self.company['target_domains']]
        if matched_keywords:
            score += 40
            reasons.append(f"业务高度匹配: {', '.join(matched_keywords)}")
        else:
            reasons.append("业务领域不匹配")

        # 2. 预算匹配 (30分)
        budget = tender_info.get('budget', 0)
        min_b, max_b = self.company['budget_range']
        if min_b <= budget <= max_b:
            score += 30
            reasons.append(f"预算符合预期 ({budget}万)")
        elif budget > max_b:
            score += 20
            reasons.append(f"预算超标 ({budget}万)，可能竞争激烈")
        elif budget > 0: # 有预算但低于下限
            score += 10
            reasons.append(f"预算偏低 ({budget}万)")
        
        # 3. 资质/技术匹配 (30分) - 简化逻辑
        # 假设只要是软件开发类，我们就默认有资质
        if "软件开发" in tender_info['tags'] or "大数据" in tender_info['tags'] or "AI/人工智能" in tender_info['tags']:
             score += 30
             reasons.append("具备相关技术资质")
        
        # 推荐建议
        recommendation = "不推荐"
        if score >= 80:
            recommendation = "强烈推荐"
        elif score >= 50:
            recommendation = "一般推荐"

        return {
            "total_score": score,
            "recommendation": recommendation,
            "match_details": reasons
        }

# ==========================================
# 4. 主程序
# ==========================================
def main():
    # 1. 加载数据
    csv_path = "../data/中国电信采购公告.csv"
    print(f">>> 正在加载招标公告数据: {csv_path} ...")
    
    try:
        df = pd.read_csv(csv_path)
        # 转换 DataFrame 为字典列表，方便后续处理
        # 填充 NaN 值为字符串
        df = df.fillna("")
        tenders = df.to_dict('records')
        print(f"    成功加载 {len(tenders)} 条记录")
    except FileNotFoundError:
        print(f"错误：找不到 {csv_path} 文件")
        return
    except Exception as e:
        print(f"读取CSV失败: {e}")
        return

    # 2. 定义公司画像
    my_company = {
        "name": "天网智能科技",
        "target_domains": ["大数据", "AI/人工智能", "软件开发", "通信/网络"],
        "budget_range": [50, 2000], # 万元 (扩大预算范围以适应更多样本)
        "qualifications": ["CMMI3", "高新技术企业"]
    }
    print(f">>> 当前公司画像: {my_company['name']}")
    print(f"    目标领域: {my_company['target_domains']}")
    print("-" * 50)

    # 3. 初始化模块
    extractor = TenderInfoExtractor()
    
    # 使用用户提供的真实 LLM 配置
    llm_api_key = "sk-claDrMA1TOAB0p5UGXyezm05S3qNhHXdB4OUzhqO7r5hh0X8"
    llm_base_url = "https://apie.zhisuaninfo.com/v1"
    llm_model = "gpt-oss-120b" # 使用用户指定的模型
    
    llm_analyzer = LLMAnalyzer(api_key=llm_api_key, base_url=llm_base_url, model=llm_model)
    
    matcher = MatchingEngine(my_company)

    results = []

    # 4. 循环处理
    # 为了演示，只取前 5 条有效数据
    count = 0
    for tender in tenders:
        if count >= 41:
            break
            
        # 清洗标题
        raw_title = str(tender.get('标题', ''))
        clean_title = extractor.clean_title(raw_title)
        
        # 获取内容，优先使用"公告内容"，如果没有则用标题代替分析
        content = str(tender.get('公告内容', ''))
        if not content or len(content) < 10:
            content = clean_title
            
        # 跳过无效数据
        if not clean_title:
            continue
            
        print(f"正在分析: {clean_title[:30]} ...")
        
        # Step 1: 规则提取
        budget = extractor.extract_budget(content)
        deadline = extractor.extract_deadline(content)
        tags = extractor.extract_keywords(content + " " + clean_title) # 结合标题和内容提取关键词
        
        # Step 2: LLM 深度分析 (模拟)
        # 传入前 500 个字符避免过长
        llm_result = llm_analyzer.analyze_with_llm(content)
        
        # Step 3: 匹配打分
        tender_info = {
            "budget": budget,
            "tags": tags,
            "deadline": deadline,
            "title": clean_title
        }
        match_result = matcher.calculate_score(tender_info)
        
        # 汇总结果
        analysis_record = {
            "id": str(tender.get('详情页ID', '')),
            "title": clean_title,
            "extracted_info": {
                "budget_wanyuan": budget,
                "deadline": deadline,
                "tags": tags
            },
            "ai_analysis": llm_result,
            "match_result": match_result
        }
        results.append(analysis_record)
        print(f"    -> 评分: {match_result['total_score']} ({match_result['recommendation']})")
        print(f"    -> 关键标签: {tags}")
        print("-" * 30)
        
        count += 1

    # 5. 输出报告
    output_file = "../data/analysis_results_real.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\n>>> 分析完成！结果已保存至 {output_file}")
    
    # 打印简要报告
    print("\n" + "="*20 + " 分析报告摘要 " + "="*20)
    for res in results:
        score = res['match_result']['total_score']
        rec = res['match_result']['recommendation']
        print(f"[{score}分] {rec} | {res['title']}")
        print(f"   原因: {'; '.join(res['match_result']['match_details'])}")
        print(f"   AI建议: {res['ai_analysis']['summary']}")
        print("-" * 50)

if __name__ == "__main__":
    main()
