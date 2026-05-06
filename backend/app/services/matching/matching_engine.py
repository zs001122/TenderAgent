from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .gate_filter import GateFilter, GateCheck, GateResult
from .ranking_engine import RankingEngine, RankingResult


@dataclass
class MatchResult:
    """匹配结果"""
    pass_gate: bool
    gate_checks: List[Dict[str, Any]]
    ranking: Optional[RankingResult]
    recommendation: str
    reason: str
    score: float = 0.0
    grade: str = "D"
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class MatchingEngine:
    """匹配引擎 - Gate + Ranking 双层结构
    
    处理流程：
    1. Gate 过滤 - 检查硬性门槛条件
    2. Ranking 评分 - 对通过 Gate 的项目进行软评分
    3. Decision 决策 - 综合给出推荐意见
    """
    
    def __init__(self, company_profile: Dict[str, Any], weights: Dict[str, float] = None):
        self.gate_filter = GateFilter(company_profile)
        self.ranking_engine = RankingEngine(company_profile, weights)
        self.company = company_profile
    
    def match(self, tender_info: Dict[str, Any]) -> MatchResult:
        """执行匹配
        
        Args:
            tender_info: 招标信息
        
        Returns:
            MatchResult: 匹配结果
        """
        gate_checks = self.gate_filter.check(tender_info)
        pass_gate = self.gate_filter.pass_gate(gate_checks)
        
        gate_checks_dict = [
            {
                'name': c.name,
                'result': c.result.value,
                'reason': c.reason,
                'is_mandatory': c.is_mandatory,
                'detail': c.detail
            }
            for c in gate_checks
        ]
        
        if not pass_gate:
            failed = self.gate_filter.get_failed_checks(gate_checks)
            reason = "; ".join([c.reason for c in failed])
            matching_details = self._build_matching_details(gate_checks, None)
            
            return MatchResult(
                pass_gate=False,
                gate_checks=gate_checks_dict,
                ranking=None,
                recommendation="不推荐",
                reason=f"未通过硬性门槛: {reason}",
                score=0.0,
                grade="D",
                confidence=1.0,
                details={
                    'failed_checks': [c.name for c in failed],
                    **matching_details,
                }
            )
        
        ranking = self.ranking_engine.calculate_score(tender_info)
        
        decision = self._make_decision(gate_checks, ranking)
        
        return MatchResult(
            pass_gate=True,
            gate_checks=gate_checks_dict,
            ranking=ranking,
            recommendation=decision['recommendation'],
            reason=decision['reason'],
            score=ranking.total_score,
            grade=ranking.grade,
            confidence=ranking.confidence,
            details={
                'warnings': [c.name for c in self.gate_filter.get_warnings(gate_checks)],
                'dimension_scores': {
                    k: {'score': v.score, 'weight': v.weight, 'details': v.details}
                    for k, v in ranking.dimension_scores.items()
                },
                **self._build_matching_details(gate_checks, ranking),
            }
        )

    def _build_matching_details(
        self,
        gate_checks: List[GateCheck],
        ranking: Optional[RankingResult],
    ) -> Dict[str, Any]:
        gate_evidence = []
        for check in gate_checks:
            status = {
                GateResult.PASS: "matched",
                GateResult.FAIL: "missing",
                GateResult.WARNING: "review",
            }.get(check.result, "review")
            gate_evidence.append({
                "dimension": "硬门槛",
                "requirement": check.detail or check.name,
                "status": status,
                "score_delta": 0,
                "matched_assets": [],
                "reason": check.reason,
                "is_mandatory": check.is_mandatory,
            })

        dimension_scores = {}
        evidence_matches = []
        if ranking:
            dimension_scores = {
                key: {
                    "name": value.name,
                    "score": value.score,
                    "weight": value.weight,
                    "details": value.details,
                }
                for key, value in ranking.dimension_scores.items()
            }
            evidence_matches = ranking.evidence_matches or []

        missing = [
            item for item in gate_evidence + evidence_matches
            if item.get("status") == "missing"
        ]
        risks = [
            item for item in gate_evidence + evidence_matches
            if item.get("status") in {"review", "weak"}
        ]
        return {
            "matching_details": {
                "dimension_scores": dimension_scores,
                "evidence_matches": evidence_matches,
                "gate_evidence": gate_evidence,
                "missing_items": missing,
                "risk_items": risks,
            }
        }
    
    def match_batch(self, tenders: List[Dict[str, Any]]) -> List[MatchResult]:
        """批量匹配"""
        return [self.match(t) for t in tenders]
    
    def _make_decision(
        self, 
        gate_checks: List[GateCheck], 
        ranking: RankingResult
    ) -> Dict[str, str]:
        """做出最终决策"""
        warnings = [c for c in gate_checks if c.result == GateResult.WARNING]
        score = ranking.total_score
        
        if score >= 80 and not warnings:
            return {
                'recommendation': '强烈推荐',
                'reason': '高分匹配，无风险提示'
            }
        elif score >= 80:
            return {
                'recommendation': '推荐',
                'reason': f"高分匹配，但有{len(warnings)}项警告需关注"
            }
        elif score >= 60:
            if warnings:
                return {
                    'recommendation': '推荐',
                    'reason': f"匹配度较高，但有{len(warnings)}项警告"
                }
            return {
                'recommendation': '推荐',
                'reason': '匹配度较高'
            }
        elif score >= 40:
            return {
                'recommendation': '观望',
                'reason': '匹配度一般，需评估投入产出比'
            }
        else:
            return {
                'recommendation': '不推荐',
                'reason': '匹配度较低'
            }
    
    def get_top_matches(
        self, 
        tenders: List[Dict[str, Any]], 
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """获取 Top N 匹配结果"""
        results = []
        
        for tender in tenders:
            match_result = self.match(tender)
            if match_result.pass_gate:
                results.append({
                    'tender': tender,
                    'match_result': match_result
                })
        
        results.sort(key=lambda x: x['match_result'].score, reverse=True)
        
        return results[:top_n]
    
    def filter_by_recommendation(
        self, 
        tenders: List[Dict[str, Any]], 
        recommendations: List[str] = None
    ) -> List[Dict[str, Any]]:
        """按推荐级别筛选"""
        if recommendations is None:
            recommendations = ['强烈推荐', '推荐']
        
        results = []
        for tender in tenders:
            match_result = self.match(tender)
            if match_result.recommendation in recommendations:
                results.append({
                    'tender': tender,
                    'match_result': match_result
                })
        
        return results


_matching_engine_instance = None


def get_matching_engine(company_profile: Dict[str, Any] = None) -> MatchingEngine:
    """获取匹配引擎实例"""
    global _matching_engine_instance
    
    if company_profile:
        _matching_engine_instance = MatchingEngine(company_profile)
    elif _matching_engine_instance is None:
        default_profile = {
            'name': '默认公司',
            'target_domains': ['软件开发', '大数据', 'AI/人工智能'],
            'budget_range': [50, 2000],
            'qualifications': ['CMMI3', '高新技术企业'],
            'service_regions': ['北京市', '上海市', '广东省'],
            'bid_history': []
        }
        _matching_engine_instance = MatchingEngine(default_profile)
    
    return _matching_engine_instance
