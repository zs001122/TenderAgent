from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .base_agent import BaseAgent, AgentResult
from .qualification_agent import QualificationAgent
from .risk_agent import RiskAgent
from .competition_agent import CompetitionAgent


@dataclass
class DecisionResult:
    """决策结果"""
    action: str
    confidence: float
    reason: str
    risks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class OrchestratorResult:
    """编排结果"""
    decision: DecisionResult
    agent_results: Dict[str, AgentResult]
    summary: str
    confidence: float


class OrchestratorAgent:
    """决策编排 Agent - 核心
    
    协调多个专业 Agent 进行分析，并做出最终决策
    
    处理流程：
    1. 调用所有注册的 Agent 进行分析
    2. 汇总分析结果
    3. 做出最终决策
    4. 生成可解释的决策说明
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.agents: List[BaseAgent] = []
        
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认 Agent"""
        self.register_agent(QualificationAgent(self.llm_client))
        self.register_agent(RiskAgent(self.llm_client))
        self.register_agent(CompetitionAgent(self.llm_client))
    
    def register_agent(self, agent: BaseAgent):
        """注册 Agent"""
        self.agents.append(agent)
    
    def analyze(
        self, 
        tender_info: Dict[str, Any], 
        company_profile: Dict[str, Any]
    ) -> OrchestratorResult:
        """执行分析并做出决策
        
        Args:
            tender_info: 招标信息
            company_profile: 公司画像
        
        Returns:
            OrchestratorResult: 编排结果
        """
        agent_results = {}
        
        for agent in self.agents:
            try:
                result = agent.analyze(tender_info, company_profile)
                agent_results[agent.name] = result
            except Exception as e:
                agent_results[agent.name] = AgentResult(
                    agent_name=agent.name,
                    analysis={'error': str(e)},
                    confidence=0.0,
                    key_findings=[f"分析失败: {str(e)}"]
                )
        
        analysis_summary = self._summarize(agent_results)
        
        decision = self._make_decision(analysis_summary, agent_results)
        
        summary = self._generate_summary(decision, agent_results)
        
        confidence = self._calculate_overall_confidence(agent_results)
        
        return OrchestratorResult(
            decision=decision,
            agent_results=agent_results,
            summary=summary,
            confidence=confidence
        )
    
    def _summarize(self, agent_results: Dict[str, AgentResult]) -> Dict[str, Any]:
        """汇总分析结果"""
        all_findings = []
        all_risks = []
        all_recommendations = []
        confidences = []
        
        for result in agent_results.values():
            all_findings.extend(result.key_findings)
            all_risks.extend(result.risks)
            all_recommendations.extend(result.recommendations)
            confidences.append(result.confidence)
        
        return {
            'total_findings': len(all_findings),
            'total_risks': len(all_risks),
            'total_recommendations': len(all_recommendations),
            'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'all_findings': all_findings,
            'all_risks': all_risks,
            'all_recommendations': all_recommendations
        }
    
    def _make_decision(
        self, 
        summary: Dict[str, Any], 
        agent_results: Dict[str, AgentResult]
    ) -> DecisionResult:
        """做出最终决策"""
        qual_result = agent_results.get('资质分析')
        risk_result = agent_results.get('风险评估')
        competition_result = agent_results.get('竞争分析')
        
        if qual_result and not qual_result.analysis.get('pass', True):
            missing = qual_result.analysis.get('missing', [])
            return DecisionResult(
                action='不投标',
                confidence=0.9,
                reason=f"缺少必要资质: {', '.join(missing)}",
                risks=qual_result.risks,
                recommendations=['建议获取缺失资质后再参与类似项目']
            )
        
        high_risks = []
        if risk_result:
            high_risks = risk_result.analysis.get('high_risk_count', 0) > 0
        
        win_prob = 0.5
        if competition_result:
            win_prob = competition_result.analysis.get('win_probability', 0.5)
        
        if high_risks and win_prob < 0.4:
            return DecisionResult(
                action='不投标',
                confidence=0.8,
                reason='高风险且中标概率低',
                risks=summary['all_risks'],
                recommendations=['建议放弃此项目']
            )
        
        if win_prob >= 0.6 and not high_risks:
            return DecisionResult(
                action='投标',
                confidence=summary['avg_confidence'],
                reason='中标概率较高，风险可控',
                risks=summary['all_risks'],
                recommendations=summary['all_recommendations']
            )
        
        if win_prob >= 0.4:
            return DecisionResult(
                action='评估后决定',
                confidence=summary['avg_confidence'],
                reason='需要进一步评估投入产出比',
                risks=summary['all_risks'],
                recommendations=summary['all_recommendations'] + ['建议详细评估项目成本和收益']
            )
        
        return DecisionResult(
            action='不投标',
            confidence=0.7,
            reason='中标概率较低',
            risks=summary['all_risks'],
            recommendations=['建议寻找更匹配的项目']
        )
    
    def _generate_summary(
        self, 
        decision: DecisionResult, 
        agent_results: Dict[str, AgentResult]
    ) -> str:
        """生成决策摘要"""
        lines = []
        
        lines.append(f"决策: {decision.action}")
        lines.append(f"置信度: {decision.confidence:.0%}")
        lines.append(f"理由: {decision.reason}")
        lines.append("")
        lines.append("详细分析:")
        
        for agent_name, result in agent_results.items():
            lines.append(f"\n【{agent_name}】")
            for finding in result.key_findings[:3]:
                lines.append(f"  - {finding}")
        
        if decision.risks:
            lines.append("\n风险提示:")
            for risk in decision.risks[:3]:
                lines.append(f"  ⚠️ {risk}")
        
        if decision.recommendations:
            lines.append("\n建议:")
            for rec in decision.recommendations[:3]:
                lines.append(f"  💡 {rec}")
        
        return "\n".join(lines)
    
    def _calculate_overall_confidence(self, agent_results: Dict[str, AgentResult]) -> float:
        """计算整体置信度"""
        if not agent_results:
            return 0.0
        
        confidences = [r.confidence for r in agent_results.values()]
        return round(sum(confidences) / len(confidences), 2)


_orchestrator_instance = None


def get_orchestrator(llm_client=None) -> OrchestratorAgent:
    """获取 Orchestrator 实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None or llm_client:
        _orchestrator_instance = OrchestratorAgent(llm_client)
    return _orchestrator_instance
