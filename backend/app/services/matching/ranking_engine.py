from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DimensionScore:
    """维度评分"""
    name: str
    score: float
    max_score: float = 100.0
    weight: float = 1.0
    details: str = ""


@dataclass
class RankingResult:
    """评分结果"""
    total_score: float
    grade: str
    dimension_scores: Dict[str, DimensionScore]
    recommendation: str
    confidence: float
    reasons: List[str]


class RankingEngine:
    """软评分层 - Ranking
    
    对通过 Gate 的项目进行多维度评分：
    1. 经验匹配 - 业务领域匹配度
    2. 预算匹配 - 预算范围符合度
    3. 历史中标概率 - 基于历史数据
    4. 竞争程度 - 行业竞争分析
    """
    
    DEFAULT_WEIGHTS = {
        'experience': 0.30,
        'budget': 0.25,
        'history': 0.25,
        'competition': 0.20,
    }
    
    def __init__(self, company_profile: Dict[str, Any], weights: Dict[str, float] = None):
        self.company = company_profile
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
    
    def calculate_score(self, tender_info: Dict[str, Any]) -> RankingResult:
        """计算综合评分
        
        Args:
            tender_info: 招标信息
        
        Returns:
            RankingResult: 评分结果
        """
        dimension_scores = {}
        reasons = []
        
        exp_score, exp_reason = self._score_experience(tender_info)
        dimension_scores['experience'] = DimensionScore(
            name='经验匹配',
            score=exp_score,
            weight=self.weights['experience'],
            details=exp_reason
        )
        if exp_reason:
            reasons.append(exp_reason)
        
        budget_score, budget_reason = self._score_budget(tender_info)
        dimension_scores['budget'] = DimensionScore(
            name='预算匹配',
            score=budget_score,
            weight=self.weights['budget'],
            details=budget_reason
        )
        if budget_reason:
            reasons.append(budget_reason)
        
        history_score, history_reason = self._score_history(tender_info)
        dimension_scores['history'] = DimensionScore(
            name='历史中标',
            score=history_score,
            weight=self.weights['history'],
            details=history_reason
        )
        if history_reason:
            reasons.append(history_reason)
        
        comp_score, comp_reason = self._score_competition(tender_info)
        dimension_scores['competition'] = DimensionScore(
            name='竞争程度',
            score=comp_score,
            weight=self.weights['competition'],
            details=comp_reason
        )
        if comp_reason:
            reasons.append(comp_reason)
        
        total_score = sum(
            dimension_scores[k].score * dimension_scores[k].weight
            for k in self.weights.keys()
        )
        
        grade = self._get_grade(total_score)
        recommendation = self._get_recommendation(total_score, dimension_scores)
        confidence = self._calculate_confidence(dimension_scores)
        
        return RankingResult(
            total_score=round(total_score, 2),
            grade=grade,
            dimension_scores=dimension_scores,
            recommendation=recommendation,
            confidence=confidence,
            reasons=reasons
        )
    
    def _score_experience(self, tender_info: Dict[str, Any]) -> tuple:
        """经验匹配评分"""
        tags = tender_info.get('tags', [])
        
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        
        company_domains = self.company.get('target_domains', [])
        
        if not tags:
            return 50.0, "无法识别业务领域"
        
        if not company_domains:
            return 50.0, "未配置公司业务领域"
        
        matched = set(tags) & set(company_domains)
        match_ratio = len(matched) / len(tags) if tags else 0
        
        if match_ratio >= 0.8:
            return 100.0, f"业务高度匹配: {', '.join(matched)}"
        elif match_ratio >= 0.5:
            return 80.0, f"业务较匹配: {', '.join(matched)}"
        elif match_ratio >= 0.3:
            return 60.0, f"业务部分匹配: {', '.join(matched)}"
        elif match_ratio > 0:
            return 40.0, f"业务少量匹配: {', '.join(matched)}"
        else:
            return 0.0, "业务领域不匹配"
    
    def _score_budget(self, tender_info: Dict[str, Any]) -> tuple:
        """预算匹配评分"""
        budget = tender_info.get('budget')
        
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        budget_range = self.company.get('budget_range', [0, float('inf')])
        min_b, max_b = budget_range[0], budget_range[1]
        
        if not budget or budget <= 0:
            return 50.0, "预算信息未知"
        
        if min_b <= budget <= max_b:
            return 100.0, f"预算符合预期 ({budget}万元)"
        
        if budget > max_b:
            over_ratio = (budget - max_b) / max_b
            if over_ratio <= 0.2:
                return 80.0, f"预算略超标 ({budget}万元)，可接受"
            elif over_ratio <= 0.5:
                return 60.0, f"预算超标 ({budget}万元)，需评估"
            else:
                return 30.0, f"预算严重超标 ({budget}万元)，风险较高"
        
        if budget < min_b:
            under_ratio = (min_b - budget) / min_b
            if under_ratio <= 0.3:
                return 70.0, f"预算偏低 ({budget}万元)，投入产出比需评估"
            else:
                return 40.0, f"预算过低 ({budget}万元)，可能不值得投入"
        
        return 50.0, "预算评估中"
    
    def _score_history(self, tender_info: Dict[str, Any]) -> tuple:
        """历史中标概率评分"""
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        
        region = tender_info.get('region', '')
        if hasattr(tender_info, 'region'):
            region = tender_info.region
        
        history_records = self.company.get('bid_history', [])
        
        if not history_records:
            return 50.0, "无历史投标记录"
        
        won_count = sum(1 for r in history_records if r.get('is_won'))
        total_count = len(history_records)
        base_rate = won_count / total_count if total_count > 0 else 0.5
        
        score = base_rate * 100
        
        return round(score, 2), f"历史中标率: {base_rate*100:.1f}% ({won_count}/{total_count})"
    
    def _score_competition(self, tender_info: Dict[str, Any]) -> tuple:
        """竞争程度评分（分数越高竞争越小）"""
        budget = tender_info.get('budget')
        if hasattr(tender_info, 'budget'):
            budget = tender_info.budget
            if hasattr(budget, 'value'):
                budget = budget.value
        
        tags = tender_info.get('tags', [])
        if hasattr(tender_info, 'tags'):
            tags = tender_info.tags
        
        score = 50.0
        reasons = []
        
        if budget:
            if budget > 1000:
                score += 10
                reasons.append("大额项目竞争可能较小")
            elif budget < 50:
                score -= 10
                reasons.append("小额项目竞争可能激烈")
        
        if 'AI/人工智能' in tags or '大数据' in tags:
            score += 5
            reasons.append("技术门槛较高，竞争相对较小")
        
        if '软件开发' in tags:
            score -= 5
            reasons.append("软件开发类项目竞争通常较激烈")
        
        score = max(0, min(100, score))
        
        return score, "; ".join(reasons) if reasons else "竞争程度中等"
    
    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"
    
    def _get_recommendation(self, total_score: float, dimension_scores: Dict[str, DimensionScore]) -> str:
        """获取推荐意见"""
        if total_score >= 80:
            return "强烈推荐"
        elif total_score >= 60:
            return "推荐"
        elif total_score >= 40:
            return "观望"
        else:
            return "不推荐"
    
    def _calculate_confidence(self, dimension_scores: Dict[str, DimensionScore]) -> float:
        """计算评分置信度"""
        scores = [ds.score for ds in dimension_scores.values()]
        
        if not scores:
            return 0.0
        
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        
        confidence = max(0.3, 1.0 - variance / 2500)
        
        return round(confidence, 2)
    
    def update_weights(self, new_weights: Dict[str, float]):
        """更新权重配置"""
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"权重总和必须为1.0，当前为{total}")
        self.weights.update(new_weights)
