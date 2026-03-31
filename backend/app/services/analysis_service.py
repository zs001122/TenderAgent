import json
import re
from typing import Dict, List, Any
from openai import OpenAI

from app.core.config import settings


class TenderInfoExtractor:
    def __init__(self):
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
        if not raw_title:
            return ""
        match = re.search(r'HYPERLINK\(".*?",\s*"(.*?)"\)', raw_title)
        if match:
            return match.group(1)
        return raw_title

    def extract_budget(self, content: str) -> float:
        if not content:
            return 0.0
        match_wan = re.search(r'(\d+(\.\d+)?)\s*万元', content)
        if match_wan:
            return float(match_wan.group(1))
        match_yi = re.search(r'(\d+(\.\d+)?)\s*亿', content)
        if match_yi:
            return float(match_yi.group(1)) * 10000
        match_yuan = re.search(r'(\d+(,\d{3})*(\.\d+)?)\s*元', content)
        if match_yuan:
            amount_str = match_yuan.group(1).replace(',', '')
            return float(amount_str) / 10000.0
        return 0.0

    def extract_deadline(self, content: str) -> str:
        if not content:
            return "未知"
        match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if match:
            return match.group(1)
        return "未知"

    def extract_keywords(self, content: str) -> List[str]:
        if not content:
            return []
        tags = set()
        for category, keywords in self.keywords_map.items():
            for kw in keywords:
                if kw in content:
                    tags.add(category)
                    break
        return list(tags)


class LLMAnalyzer:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def analyze_with_llm(self, tender_text: str) -> Dict[str, Any]:
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
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r'(\{.*\})', content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        pass
                print(f"DEBUG: JSON解析失败，原始内容: {content[:200]}...")
                raise
            
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return {
                "risk_assessment": "分析失败",
                "competitor_analysis": "未知",
                "technical_difficulty": "未知",
                "summary": f"API调用出错: {str(e)[:50]}..."
            }


class MatchingEngine:
    def __init__(self, company_profile: Dict):
        self.company = company_profile

    def calculate_score(self, tender_info: Dict) -> Dict:
        score = 0
        reasons = []

        matched_keywords = [tag for tag in tender_info.get('tags', []) if tag in self.company['target_domains']]
        if matched_keywords:
            score += 40
            reasons.append(f"业务高度匹配: {', '.join(matched_keywords)}")
        else:
            reasons.append("业务领域不匹配")

        budget = tender_info.get('budget', 0)
        min_b, max_b = self.company['budget_range']
        if min_b <= budget <= max_b:
            score += 30
            reasons.append(f"预算符合预期 ({budget}万)")
        elif budget > max_b:
            score += 20
            reasons.append(f"预算超标 ({budget}万)，可能竞争激烈")
        elif budget > 0:
            score += 10
            reasons.append(f"预算偏低 ({budget}万)")
        
        tags = tender_info.get('tags', [])
        if "软件开发" in tags or "大数据" in tags or "AI/人工智能" in tags:
            score += 30
            reasons.append("具备相关技术资质")
        
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


class AnalysisService:
    def __init__(self):
        self.extractor = TenderInfoExtractor()
        
        self.llm_api_key = settings.LLM_API_KEY
        self.llm_base_url = settings.LLM_BASE_URL
        self.llm_model = settings.LLM_MODEL
        
        self.llm_analyzer = LLMAnalyzer(
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
            model=self.llm_model
        )
        
        self.my_company = {
            "name": "天网智能科技",
            "target_domains": ["大数据", "AI/人工智能", "软件开发", "通信/网络"],
            "budget_range": [50, 2000],
            "qualifications": ["CMMI3", "高新技术企业"]
        }
        self.matcher = MatchingEngine(self.my_company)

    def analyze_tender(self, tender: Dict) -> Dict:
        clean_title = tender.get('clean_title', '') or tender.get('title', '')
        content = str(tender.get('content', ''))
        if not content or len(content) < 10:
            content = clean_title
            
        budget = self.extractor.extract_budget(content)
        deadline = self.extractor.extract_deadline(content)
        tags = self.extractor.extract_keywords(content + " " + clean_title)
        
        llm_result = self.llm_analyzer.analyze_with_llm(content[:1000])
        
        tender_info = {
            "budget": budget,
            "tags": tags,
            "deadline": deadline,
            "title": clean_title
        }
        match_result = self.matcher.calculate_score(tender_info)
        
        return {
            "id": str(tender.get('id', '')),
            "title": clean_title,
            "extracted_info": {
                "budget_wanyuan": budget,
                "deadline": deadline,
                "tags": tags
            },
            "ai_analysis": llm_result,
            "match_result": match_result
        }


_service_instance = None

def get_analysis_service():
    global _service_instance
    if _service_instance is None:
        _service_instance = AnalysisService()
    return _service_instance
