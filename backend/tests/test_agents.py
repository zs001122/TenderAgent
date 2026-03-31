import pytest

from app.agents.base_agent import BaseAgent, AgentResult
from app.agents.qualification_agent import QualificationAgent
from app.agents.risk_agent import RiskAgent
from app.agents.competition_agent import CompetitionAgent
from app.agents.orchestrator import OrchestratorAgent, OrchestratorResult, DecisionResult


class TestQualificationAgent:
    """资质分析 Agent 测试"""

    def setup_method(self):
        self.agent = QualificationAgent()

    def test_agent_name(self):
        assert self.agent.name == '资质分析'

    def test_analyze_match(self, sample_tender_info, sample_company_profile):
        result = self.agent.analyze(sample_tender_info, sample_company_profile)
        
        assert isinstance(result, AgentResult)
        assert result.agent_name == '资质分析'
        assert result.confidence >= 0
        assert len(result.key_findings) > 0

    def test_analyze_missing_qualification(self, sample_company_profile):
        tender = {
            'title': '高要求项目',
            'qualifications': ['CMMI5', 'ISO9001', '特殊资质'],
        }
        result = self.agent.analyze(tender, sample_company_profile)
        
        assert result.analysis.get('pass') == False or len(result.analysis.get('missing', [])) > 0

    def test_analyze_all_match(self, sample_tender_info, sample_company_profile):
        result = self.agent.analyze(sample_tender_info, sample_company_profile)
        
        assert result.analysis.get('pass') == True


class TestRiskAgent:
    """风险评估 Agent 测试"""

    def setup_method(self):
        self.agent = RiskAgent()

    def test_agent_name(self):
        assert self.agent.name == '风险评估'

    def test_analyze_risks(self, sample_tender_info, sample_company_profile):
        result = self.agent.analyze(sample_tender_info, sample_company_profile)
        
        assert isinstance(result, AgentResult)
        assert result.agent_name == '风险评估'
        assert 'risks' in result.analysis or len(result.risks) >= 0

    def test_time_risk_assessment(self, sample_company_profile):
        from datetime import datetime, timedelta
        
        urgent_tender = {
            'title': '紧急项目',
            'deadline': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'budget': 500,
        }
        result = self.agent.analyze(urgent_tender, sample_company_profile)
        
        assert result.confidence >= 0


class TestCompetitionAgent:
    """竞争分析 Agent 测试"""

    def setup_method(self):
        self.agent = CompetitionAgent()

    def test_agent_name(self):
        assert self.agent.name == '竞争分析'

    def test_analyze_competition(self, sample_tender_info, sample_company_profile):
        result = self.agent.analyze(sample_tender_info, sample_company_profile)
        
        assert isinstance(result, AgentResult)
        assert result.agent_name == '竞争分析'
        assert 'win_probability' in result.analysis

    def test_win_probability_range(self, sample_tender_info, sample_company_profile):
        result = self.agent.analyze(sample_tender_info, sample_company_profile)
        
        win_prob = result.analysis.get('win_probability', 0)
        assert 0 <= win_prob <= 1


class TestOrchestratorAgent:
    """Orchestrator 决策 Agent 测试"""

    def setup_method(self):
        self.orchestrator = OrchestratorAgent()

    def test_registered_agents(self):
        agent_names = [agent.name for agent in self.orchestrator.agents]
        assert '资质分析' in agent_names
        assert '风险评估' in agent_names
        assert '竞争分析' in agent_names

    def test_analyze_returns_orchestrator_result(self, sample_tender_info, sample_company_profile):
        result = self.orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert isinstance(result, OrchestratorResult)
        assert isinstance(result.decision, DecisionResult)
        assert result.decision.action in ['投标', '不投标', '评估后决定']
        assert result.confidence >= 0

    def test_analyze_generates_summary(self, sample_tender_info, sample_company_profile):
        result = self.orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert result.summary != ''
        assert '决策' in result.summary

    def test_analyze_collects_all_agent_results(self, sample_tender_info, sample_company_profile):
        result = self.orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert '资质分析' in result.agent_results
        assert '风险评估' in result.agent_results
        assert '竞争分析' in result.agent_results

    def test_decision_for_good_match(self, sample_tender_info, sample_company_profile):
        result = self.orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert result.decision.action in ['投标', '评估后决定']

    def test_decision_for_poor_match(self, sample_company_profile):
        poor_tender = {
            'title': '不匹配项目',
            'qualifications': ['CMMI5', '特殊资质X'],
            'budget': 5000,
            'region': '新疆省',
        }
        result = self.orchestrator.analyze(poor_tender, sample_company_profile)
        
        assert result.decision.action == '不投标'

    def test_decision_has_reason(self, sample_tender_info, sample_company_profile):
        result = self.orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert result.decision.reason != ''
