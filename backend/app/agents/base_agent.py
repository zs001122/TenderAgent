from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    """Agent 分析结果"""
    agent_name: str
    analysis: Dict[str, Any]
    confidence: float
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Agent 基类
    
    所有专业 Agent 都需要继承此类并实现 analyze 方法
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称"""
        pass
    
    @property
    def description(self) -> str:
        """Agent 描述"""
        return ""
    
    @abstractmethod
    def analyze(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> AgentResult:
        """执行分析
        
        Args:
            tender_info: 招标信息
            company_profile: 公司画像
        
        Returns:
            AgentResult: 分析结果
        """
        pass
    
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """调用 LLM"""
        if not self.llm_client:
            return ""
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.llm_client.chat.completions.create(
                model=getattr(self.llm_client, 'model', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return ""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """从 LLM 响应中提取 JSON"""
        import json
        import re
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        return {}
