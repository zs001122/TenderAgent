import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.extraction.pipeline import InformationFusionPipeline
from app.services.matching.matching_engine import MatchingEngine
from app.agents.orchestrator import OrchestratorAgent


class TestEndToEnd:
    """端到端集成测试 - 验证完整流程"""

    def test_full_pipeline_extraction_to_decision(
        self, sample_tender_content, sample_company_profile
    ):
        extraction_pipeline = InformationFusionPipeline()
        matching_engine = MatchingEngine(sample_company_profile)
        orchestrator = OrchestratorAgent()
        
        result = extraction_pipeline.extract(sample_tender_content)
        
        assert result.success == True
        
        tender_info = {
            'title': '某市大数据平台建设项目',
            'budget': result.info.budget.value if result.info.budget else 0,
            'deadline': result.info.deadline.value.strftime('%Y-%m-%d') if result.info.deadline and result.info.deadline.value else None,
            'region': result.info.region,
            'qualifications': result.info.qualifications.required if result.info.qualifications else [],
            'tags': result.info.tags,
            'content': sample_tender_content
        }
        
        match_result = matching_engine.match(tender_info)
        
        assert match_result.pass_gate == True
        
        orchestrator_result = orchestrator.analyze(tender_info, sample_company_profile)
        
        assert orchestrator_result.decision.action in ['投标', '评估后决定']

    def test_full_pipeline_with_poor_match(
        self, sample_company_profile
    ):
        extraction_pipeline = InformationFusionPipeline()
        matching_engine = MatchingEngine(sample_company_profile)
        orchestrator = OrchestratorAgent()
        
        poor_content = """
        某工程招标公告
        
        项目预算：5000万元
        项目地点：新疆省
        
        资质要求：
        1. 特种工程资质
        2. 一级建造师
        
        截止时间：2026年5月1日
        """
        
        extraction_result = extraction_pipeline.extract(poor_content)
        
        tender_info = {
            'title': '某工程招标',
            'budget': extraction_result.info.budget.value if extraction_result.info.budget else 0,
            'region': extraction_result.info.region,
            'qualifications': extraction_result.info.qualifications.required if extraction_result.info.qualifications else [],
            'deadline': '2026-05-01'
        }
        
        match_result = matching_engine.match(tender_info)
        
        orchestrator_result = orchestrator.analyze(tender_info, sample_company_profile)
        
        assert match_result.pass_gate == False or orchestrator_result.decision.action == '不投标'

    def test_batch_processing(self, sample_company_profile):
        extraction_pipeline = InformationFusionPipeline()
        matching_engine = MatchingEngine(sample_company_profile)
        
        tenders_content = [
            "采购预算：100万元，截止时间：2026年5月1日，项目地点：广东省",
            "项目金额：500万元，投标截止：2026年6月1日，项目地点：北京市",
            "预算：2000万元，截止：2026年7月1日，项目地点：上海市",
        ]
        
        extraction_results = extraction_pipeline.extract_batch(
            [{'content': c} for c in tenders_content]
        )
        
        assert len(extraction_results) == 3
        
        tender_infos = []
        future_deadline = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        for i, result in enumerate(extraction_results):
            tender_infos.append({
                'title': f'项目{i+1}',
                'budget': result.info.budget.value if result.info.budget else 0,
                'region': result.info.region,
                'deadline': future_deadline,
                'qualifications': []
            })
        
        match_results = matching_engine.match_batch(tender_infos)
        
        assert len(match_results) == 3
        
        passed = [r for r in match_results if r.pass_gate]
        assert len(passed) > 0

    def test_quick_analysis_flow(self, sample_tender_content, sample_company_profile):
        extraction_pipeline = InformationFusionPipeline()
        matching_engine = MatchingEngine(sample_company_profile)
        
        quick_result = extraction_pipeline.quick_extract(sample_tender_content)
        
        assert quick_result['budget'] is not None
        
        tender_info = {
            'budget': quick_result['budget'],
            'deadline': quick_result['deadline'],
            'qualifications': quick_result['qualifications'],
            'tags': quick_result['tags']
        }
        
        match_result = matching_engine.match(tender_info)
        
        assert match_result is not None


class TestKnowledgeGraphIntegration:
    """知识图谱集成测试"""

    def test_qualification_mapping_in_matching(self, sample_company_profile):
        from app.knowledge.qualification_mapping import QualificationMapping
        
        tender = {
            'qualifications': ['CMMI三级', '信息安全管理体系认证'],
            'budget': 500,
            'region': '广东省',
            'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        }
        
        normalized_quals = [
            QualificationMapping.normalize(q) for q in tender['qualifications']
        ]
        
        assert 'CMMI3' in normalized_quals
        assert 'ISO27001' in normalized_quals

    def test_industry_classification(self):
        from app.knowledge.industry_classification import IndustryClassification
        
        result = IndustryClassification.classify_keywords(['大数据', 'AI', '机器学习'])
        
        assert result is not None
        assert isinstance(result, dict)

    def test_company_relation_graph(self):
        from app.knowledge.company_relation import CompanyRelationGraph
        
        graph = CompanyRelationGraph()
        
        competitors = graph.get_competitors('测试公司')
        assert isinstance(competitors, list)


class TestFeedbackLoopIntegration:
    """反馈学习集成测试"""

    def test_feedback_learner_with_mock(self):
        from app.services.feedback_learner import FeedbackLearner
        
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        
        learner = FeedbackLearner(db_session=mock_session)
        
        assert learner is not None
        assert learner.db is mock_session
