from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResult


class CompetitionAgent(BaseAgent):
    """竞争分析 Agent
    
    分析项目的竞争态势
    """
    
    @property
    def name(self) -> str:
        return "竞争分析"
    
    @property
    def description(self) -> str:
        return "分析项目的竞争态势，评估中标概率"
    
    def analyze(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> AgentResult:
        key_findings = []
        recommendations = []
        
        competition_level = self._assess_competition_level(tender_info)
        key_findings.append(f"竞争程度: {competition_level}")
        
        win_probability = self._estimate_win_probability(tender_info, company_profile)
        key_findings.append(f"预估中标概率: {win_probability*100:.0f}%")
        
        advantages = self._identify_advantages(tender_info, company_profile)
        if advantages:
            key_findings.append(f"竞争优势: {', '.join(advantages)}")
        
        disadvantages = self._identify_disadvantages(tender_info, company_profile)
        if disadvantages:
            key_findings.append(f"竞争劣势: {', '.join(disadvantages)}")
            recommendations.append("建议针对劣势制定应对策略")
        
        if win_probability >= 0.6:
            recommendations.append("中标概率较高，建议积极参与")
        elif win_probability >= 0.4:
            recommendations.append("中标概率中等，建议评估投入")
        else:
            recommendations.append("中标概率较低，建议谨慎决策")
        
        confidence = self._calculate_confidence(tender_info, company_profile)
        
        return AgentResult(
            agent_name=self.name,
            analysis={
                'competition_level': competition_level,
                'win_probability': win_probability,
                'advantages': advantages,
                'disadvantages': disadvantages
            },
            confidence=confidence,
            key_findings=key_findings,
            recommendations=recommendations
        )
    
    def _assess_competition_level(self, tender_info: Dict[str, Any]) -> str:
        """评估竞争程度"""
        budget = tender_info.get('budget')
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        
        score = 50
        
        if budget:
            if budget > 500:
                score -= 15
            elif budget > 100:
                score -= 5
            elif budget < 30:
                score += 15
        
        if 'AI/人工智能' in tags or '大数据' in tags:
            score -= 10
        if '软件开发' in tags:
            score += 10
        if '硬件/设备' in tags:
            score += 15
        
        if score >= 70:
            return "激烈"
        elif score >= 40:
            return "中等"
        else:
            return "较小"
    
    def _estimate_win_probability(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> float:
        """预估中标概率"""
        base_prob = 0.3
        
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        company_domains = company_profile.get('target_domains', [])
        
        if tags and company_domains:
            match_ratio = len(set(tags) & set(company_domains)) / len(tags)
            base_prob += match_ratio * 0.3
        
        budget = tender_info.get('budget')
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        budget_range = company_profile.get('budget_range', [0, float('inf')])
        
        if budget and budget_range[0] <= budget <= budget_range[1]:
            base_prob += 0.15
        
        quals = tender_info.get('qualifications', [])
        if hasattr(tender_info, 'qualifications'):
            qual_obj = tender_info.qualifications
            if hasattr(qual_obj, 'required'):
                quals = qual_obj.required
        company_quals = company_profile.get('qualifications', [])
        
        if quals and company_quals:
            qual_match = len(set(quals) & set(company_quals)) / len(quals)
            base_prob += qual_match * 0.25
        
        return min(0.95, max(0.05, base_prob))
    
    def _identify_advantages(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> List[str]:
        """识别竞争优势"""
        advantages = []
        
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        company_domains = company_profile.get('target_domains', [])
        
        matched = set(tags) & set(company_domains)
        if matched:
            advantages.append(f"业务领域匹配({len(matched)}项)")
        
        company_quals = company_profile.get('qualifications', [])
        if company_quals:
            advantages.append(f"具备{len(company_quals)}项资质")
        
        history = company_profile.get('bid_history', [])
        if history:
            won = sum(1 for h in history if h.get('is_won'))
            if won > 0:
                advantages.append(f"有{won}次中标经验")
        
        return advantages
    
    def _identify_disadvantages(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> List[str]:
        """识别竞争劣势"""
        disadvantages = []
        
        quals = tender_info.get('qualifications', [])
        if hasattr(tender_info, 'qualifications'):
            qual_obj = tender_info.qualifications
            if hasattr(qual_obj, 'required'):
                quals = qual_obj.required
        company_quals = set(company_profile.get('qualifications', []))
        
        missing = set(quals) - company_quals if quals else set()
        if missing:
            disadvantages.append(f"缺少{len(missing)}项资质")
        
        budget = tender_info.get('budget')
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        budget_range = company_profile.get('budget_range', [0, float('inf')])
        
        if budget and budget > budget_range[1]:
            disadvantages.append("预算超出能力范围")
        
        return disadvantages
    
    def _calculate_confidence(self, tender_info: Dict[str, Any], company_profile: Dict[str, Any]) -> float:
        """计算置信度"""
        confidence = 0.5
        
        if tender_info.get('budget') or (hasattr(tender_info, 'budget') and tender_info.budget):
            confidence += 0.1
        if tender_info.get('tags') or (hasattr(tender_info, 'tags') and tender_info.tags):
            confidence += 0.1
        if company_profile.get('bid_history'):
            confidence += 0.2
        
        return min(0.9, confidence)
