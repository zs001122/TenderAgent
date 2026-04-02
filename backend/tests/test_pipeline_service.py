import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.pipeline_service import PipelineService
from app.models.tender import Tender
from app.models.analysis import AnalysisResult
from app.db.repository import TenderRepository, CompanyRepository


class TestPipelineService:
    """PipelineService 集成测试"""

    def test_process_tender_basic(self):
        """测试基本处理流程"""
        mock_session = MagicMock()
        mock_tender = Tender(
            id=1,
            title="测试招标项目",
            source_url="http://test.com/1",
            source_site="测试站点",
            publish_date=datetime.now(),
            content="""
            项目名称：测试大数据平台项目
            采购预算：500万元
            投标截止时间：2026年5月1日
            项目地点：广东省深圳市
            资质要求：CMMI3级、ISO27001认证
            联系人：张经理，电话：0755-12345678
            """
        )
        
        mock_session.get.return_value = mock_tender
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        
        company_profile = {
            "name": "测试公司",
            "target_domains": ["软件开发", "大数据"],
            "budget_range": [50, 1000],
            "qualifications": ["CMMI3", "ISO27001"],
            "service_regions": ["广东省", "北京市"],
            "bid_history": []
        }
        
        service = PipelineService(mock_session, company_profile)
        
        with patch.object(service.tender_repo, 'update_extraction_result'):
            with patch.object(service.tender_repo, 'save_analysis_result', return_value=AnalysisResult(
                id=1,
                tender_id=1,
                pass_gate=True,
                match_score=85.0,
                match_grade="A",
                recommendation="强烈推荐",
                decision_action="投标",
                decision_confidence=0.85
            )):
                result = service.process_tender(1)
        
        assert result is not None

    def test_get_full_analysis(self):
        """测试获取完整分析结果"""
        mock_session = MagicMock()
        
        tender_dict = {
            "id": 1,
            "title": "测试项目",
            "source_url": "http://test.com/1",
            "publish_date": "2026-04-01",
            "budget_amount": 500,
            "deadline": "2026-05-01",
            "qualifications": ["CMMI3"],
            "tags": ["大数据"],
        }
        
        analysis_dict = {
            "id": 1,
            "tender_id": 1,
            "pass_gate": True,
            "match_score": 85.0,
            "match_grade": "A",
            "recommendation": "强烈推荐",
            "decision_action": "投标",
            "decision_confidence": 0.85,
        }
        
        company_profile = {
            "name": "测试公司",
            "target_domains": ["软件开发"],
            "budget_range": [50, 1000],
            "qualifications": ["CMMI3"],
            "service_regions": ["广东省"],
            "bid_history": []
        }
        
        with patch.object(TenderRepository, 'get_tender_dict_by_id', return_value=tender_dict):
            with patch.object(TenderRepository, 'get_analysis_result', return_value=analysis_dict):
                service = PipelineService(mock_session, company_profile)
                result = service.get_full_analysis(1)
        
        assert result is not None
        assert result["tender_id"] == 1
        assert result["title"] == "测试项目"
        assert result["matching"]["pass_gate"] == True


class TestTenderRepository:
    """TenderRepository 测试"""

    def test_get_unanalyzed_tenders(self):
        """测试获取未分析招标"""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []
        
        repo = TenderRepository(mock_session)
        result = repo.get_unanalyzed_tenders(limit=10)
        
        assert isinstance(result, list)

    def test_get_recommended_tenders(self):
        """测试获取推荐招标"""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []
        
        repo = TenderRepository(mock_session)
        result = repo.get_recommended_tenders(min_score=60.0, limit=10)
        
        assert isinstance(result, list)


class TestCompanyRepository:
    """CompanyRepository 测试"""

    def test_get_profile_dict(self):
        """测试获取公司画像"""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        
        repo = CompanyRepository(mock_session)
        result = repo.get_profile_dict()
        
        assert "name" in result
        assert "budget_range" in result
        assert "qualifications" in result

    def test_default_profile(self):
        """测试默认画像"""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        
        repo = CompanyRepository(mock_session)
        result = repo._default_profile()
        
        assert result["name"] == "默认公司"
        assert len(result["budget_range"]) == 2


class TestEndToEndFlow:
    """端到端流程测试"""

    def test_extraction_to_matching_flow(self, sample_tender_content, sample_company_profile):
        """测试提取到匹配的完整流程"""
        from app.services.extraction.pipeline import InformationFusionPipeline
        from app.services.matching.matching_engine import MatchingEngine
        
        pipeline = InformationFusionPipeline()
        extraction_result = pipeline.extract(sample_tender_content)
        
        assert extraction_result.success == True
        
        tender_info = {
            'title': '某市大数据平台建设项目',
            'budget': extraction_result.info.budget.value if extraction_result.info.budget else None,
            'deadline': extraction_result.info.deadline.value.strftime('%Y-%m-%d') if extraction_result.info.deadline and extraction_result.info.deadline.value else None,
            'region': extraction_result.info.region,
            'qualifications': extraction_result.info.qualifications.required if extraction_result.info.qualifications else [],
            'tags': extraction_result.tags if hasattr(extraction_result, 'tags') else [],
        }
        
        engine = MatchingEngine(sample_company_profile)
        match_result = engine.match(tender_info)
        
        assert match_result.pass_gate == True
        assert match_result.score > 0

    def test_matching_to_agent_flow(self, sample_tender_info, sample_company_profile):
        """测试匹配到Agent决策的流程"""
        from app.services.matching.matching_engine import MatchingEngine
        from app.agents.orchestrator import OrchestratorAgent
        
        engine = MatchingEngine(sample_company_profile)
        match_result = engine.match(sample_tender_info)
        
        orchestrator = OrchestratorAgent()
        orchestrator_result = orchestrator.analyze(sample_tender_info, sample_company_profile)
        
        assert orchestrator_result.decision.action in ['投标', '不投标', '评估后决定']
