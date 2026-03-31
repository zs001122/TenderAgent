from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentResult


class RiskAgent(BaseAgent):
    """风险评估 Agent
    
    评估投标项目的各类风险
    """
    
    @property
    def name(self) -> str:
        return "风险评估"
    
    @property
    def description(self) -> str:
        return "评估投标项目的各类风险，包括时间风险、预算风险、技术风险等"
    
    def analyze(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> AgentResult:
        risks = []
        key_findings = []
        recommendations = []
        
        time_risk = self._assess_time_risk(tender_info)
        if time_risk:
            risks.append(time_risk)
            key_findings.append(time_risk['description'])
        
        budget_risk = self._assess_budget_risk(tender_info, company_profile)
        if budget_risk:
            risks.append(budget_risk)
            key_findings.append(budget_risk['description'])
        
        tech_risk = self._assess_technical_risk(tender_info, company_profile)
        if tech_risk:
            risks.append(tech_risk)
            key_findings.append(tech_risk['description'])
        
        competition_risk = self._assess_competition_risk(tender_info)
        if competition_risk:
            risks.append(competition_risk)
            key_findings.append(competition_risk['description'])
        
        high_risks = [r for r in risks if r['level'] == '高']
        medium_risks = [r for r in risks if r['level'] == '中']
        
        if high_risks:
            recommendations.append(f"存在{len(high_risks)}项高风险，建议谨慎评估")
        if medium_risks:
            recommendations.append(f"存在{len(medium_risks)}项中风险，需要关注")
        
        confidence = self._calculate_confidence(risks)
        
        return AgentResult(
            agent_name=self.name,
            analysis={
                'risks': risks,
                'high_risk_count': len(high_risks),
                'medium_risk_count': len(medium_risks),
                'total_risk_count': len(risks)
            },
            confidence=confidence,
            key_findings=key_findings if key_findings else ["未发现明显风险"],
            recommendations=recommendations,
            risks=[r['description'] for r in high_risks]
        )
    
    def _assess_time_risk(self, tender_info: Dict[str, Any]) -> Dict[str, Any]:
        """评估时间风险"""
        deadline = tender_info.get('deadline')
        
        if hasattr(tender_info, 'deadline'):
            deadline = tender_info.deadline
            if hasattr(deadline, 'value'):
                deadline = deadline.value
        
        if not deadline:
            return {
                'type': '时间风险',
                'level': '中',
                'description': '无法获取投标截止时间'
            }
        
        if isinstance(deadline, str):
            try:
                deadline = datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                return {
                    'type': '时间风险',
                    'level': '中',
                    'description': '投标截止时间格式异常'
                }
        
        days_left = (deadline - datetime.now()).days
        
        if days_left < 0:
            return {
                'type': '时间风险',
                'level': '高',
                'description': f'已过投标截止时间 {abs(days_left)} 天'
            }
        elif days_left < 3:
            return {
                'type': '时间风险',
                'level': '高',
                'description': f'投标时间紧迫，仅剩 {days_left} 天'
            }
        elif days_left < 7:
            return {
                'type': '时间风险',
                'level': '中',
                'description': f'投标时间较紧，剩余 {days_left} 天'
            }
        
        return None
    
    def _assess_budget_risk(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """评估预算风险"""
        budget = tender_info.get('budget')
        
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        if not budget:
            return {
                'type': '预算风险',
                'level': '中',
                'description': '预算信息不明确'
            }
        
        budget_range = company_profile.get('budget_range', [0, float('inf')])
        min_b, max_b = budget_range[0], budget_range[1]
        
        if budget > max_b * 1.5:
            return {
                'type': '预算风险',
                'level': '高',
                'description': f'预算严重超标 ({budget}万元)，超出能力范围'
            }
        elif budget > max_b:
            return {
                'type': '预算风险',
                'level': '中',
                'description': f'预算超标 ({budget}万元)，需评估承接能力'
            }
        elif budget < min_b * 0.5:
            return {
                'type': '预算风险',
                'level': '中',
                'description': f'预算偏低 ({budget}万元)，投入产出比需评估'
            }
        
        return None
    
    def _assess_technical_risk(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """评估技术风险"""
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        
        company_domains = company_profile.get('target_domains', [])
        
        if not tags:
            return None
        
        unmatched = set(tags) - set(company_domains)
        
        if len(unmatched) == len(tags):
            return {
                'type': '技术风险',
                'level': '高',
                'description': f'业务领域完全不匹配: {", ".join(tags)}'
            }
        elif len(unmatched) > len(tags) * 0.5:
            return {
                'type': '技术风险',
                'level': '中',
                'description': f'部分业务领域不熟悉: {", ".join(unmatched)}'
            }
        
        return None
    
    def _assess_competition_risk(self, tender_info: Dict[str, Any]) -> Dict[str, Any]:
        """评估竞争风险"""
        budget = tender_info.get('budget')
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        if budget and budget < 30:
            return {
                'type': '竞争风险',
                'level': '中',
                'description': '小额项目竞争可能激烈'
            }
        
        return None
    
    def _calculate_confidence(self, risks: List[Dict]) -> float:
        """计算置信度"""
        if not risks:
            return 0.9
        
        high_count = sum(1 for r in risks if r['level'] == '高')
        
        if high_count > 0:
            return max(0.5, 0.9 - high_count * 0.1)
        
        return 0.8
