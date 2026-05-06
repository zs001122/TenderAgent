import pytest
from datetime import datetime, timedelta

from app.services.matching.gate_filter import GateFilter, GateResult
from app.services.matching.ranking_engine import RankingEngine
from app.services.matching.matching_engine import MatchingEngine, MatchResult


class TestGateFilter:
    """Gate 过滤层测试"""

    def test_qualification_gate_pass(self, sample_company_profile, sample_tender_info):
        gate_filter = GateFilter(sample_company_profile)
        checks = gate_filter.check(sample_tender_info)
        
        qual_checks = [c for c in checks if '资质' in c.name]
        assert len(qual_checks) > 0
        for check in qual_checks:
            assert check.result == GateResult.PASS

    def test_qualification_gate_fail(self, sample_company_profile):
        gate_filter = GateFilter(sample_company_profile)
        tender = {
            'qualifications': ['CMMI5', 'ISO9001', '未知资质'],
            'region': '广东省',
            'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'budget': 500
        }
        checks = gate_filter.check(tender)
        
        qual_checks = [c for c in checks if '资质' in c.name]
        failed_checks = [c for c in qual_checks if c.result == GateResult.FAIL]
        assert len(failed_checks) > 0

    def test_region_gate_pass(self, sample_company_profile, sample_tender_info):
        gate_filter = GateFilter(sample_company_profile)
        checks = gate_filter.check(sample_tender_info)
        
        region_check = next((c for c in checks if '地域' in c.name), None)
        assert region_check is not None
        assert region_check.result == GateResult.PASS

    def test_deadline_gate_pass(self, sample_company_profile):
        gate_filter = GateFilter(sample_company_profile)
        tender = {
            'qualifications': [],
            'region': '广东省',
            'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'budget': 500
        }
        checks = gate_filter.check(tender)
        deadline_check = next((c for c in checks if '截止' in c.name), None)
        assert deadline_check is not None
        assert deadline_check.result == GateResult.PASS

    def test_deadline_gate_fail(self, sample_company_profile):
        gate_filter = GateFilter(sample_company_profile)
        tender = {
            'qualifications': [],
            'region': '广东省',
            'deadline': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'budget': 500
        }
        checks = gate_filter.check(tender)
        deadline_check = next((c for c in checks if '截止' in c.name), None)
        assert deadline_check is not None
        assert deadline_check.result == GateResult.FAIL

    def test_budget_gate_pass(self, sample_company_profile):
        gate_filter = GateFilter(sample_company_profile)
        tender = {
            'qualifications': [],
            'region': '广东省',
            'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            'budget': 500
        }
        checks = gate_filter.check(tender)
        budget_check = next((c for c in checks if '预算' in c.name), None)
        assert budget_check is not None
        assert budget_check.result == GateResult.PASS


class TestRankingEngine:
    """Ranking 评分层测试"""

    def test_calculate_score(self, sample_company_profile, sample_tender_info):
        ranking_engine = RankingEngine(sample_company_profile)
        result = ranking_engine.calculate_score(sample_tender_info)
        
        assert result.total_score >= 0
        assert result.total_score <= 100
        assert result.grade in ['A', 'B', 'C', 'D']
        assert len(result.dimension_scores) > 0

    def test_experience_dimension(self, sample_company_profile, sample_tender_info):
        ranking_engine = RankingEngine(sample_company_profile)
        result = ranking_engine.calculate_score(sample_tender_info)
        
        assert 'experience' in result.dimension_scores
        exp_score = result.dimension_scores['experience']
        assert exp_score.score >= 0

    def test_budget_dimension(self, sample_company_profile, sample_tender_info):
        ranking_engine = RankingEngine(sample_company_profile)
        result = ranking_engine.calculate_score(sample_tender_info)
        
        assert 'budget' in result.dimension_scores

    def test_asset_evidence_ignores_empty_asset_fields(self, sample_company_profile):
        sample_company_profile["assets"] = [
            {
                "asset_type": "project_case",
                "name": "Data governance platform",
                "category": None,
                "issuer": None,
                "keywords": ["data", "governance"],
                "data": {"summary": None, "scope": "platform delivery"},
            }
        ]
        ranking_engine = RankingEngine(sample_company_profile)

        result = ranking_engine.calculate_score({
            "title": "Data governance platform",
            "tags": ["data", "governance"],
            "content": "platform delivery",
            "budget": 500,
        })

        assert result.dimension_scores["evidence"].score > 0


class TestMatchingEngine:
    """匹配引擎集成测试"""

    def test_match_pass_gate(self, sample_company_profile, sample_tender_info):
        engine = MatchingEngine(sample_company_profile)
        result = engine.match(sample_tender_info)
        
        assert isinstance(result, MatchResult)
        assert result.pass_gate == True
        assert result.score > 0
        assert result.recommendation in ['强烈推荐', '推荐', '观望', '不推荐']

    def test_match_uses_imported_asset_evidence(self, sample_company_profile, sample_tender_info):
        sample_company_profile["assets"] = [
            {
                "asset_type": "qualification",
                "source_sheet": "专业资质认证",
                "name": "CMMI-Level 5",
                "status": "有效",
                "keywords": [],
                "data": {},
            },
            {
                "asset_type": "project_case",
                "source_sheet": "业绩",
                "name": "大数据平台开发服务合同",
                "status": "有效",
                "keywords": ["大数据", "软件开发"],
                "data": {"合同摘要": "大数据平台开发、数据治理"},
            },
        ]
        sample_tender_info["qualifications"] = ["CMMI5"]

        result = MatchingEngine(sample_company_profile).match(sample_tender_info)

        assert result.pass_gate is True
        assert "evidence" in result.details["dimension_scores"]
        assert result.details["dimension_scores"]["evidence"]["score"] > 50

    def test_match_fail_gate(self, sample_company_profile):
        engine = MatchingEngine(sample_company_profile)
        tender = {
            'qualifications': ['CMMI5', '未知资质'],
            'region': '新疆省',
            'deadline': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'budget': 5000
        }
        result = engine.match(tender)
        
        assert result.pass_gate == False
        assert result.recommendation == '不推荐'

    def test_match_batch(self, sample_company_profile, sample_tender_info):
        engine = MatchingEngine(sample_company_profile)
        tenders = [sample_tender_info, sample_tender_info]
        results = engine.match_batch(tenders)
        
        assert len(results) == 2
        assert all(isinstance(r, MatchResult) for r in results)

    def test_get_top_matches(self, sample_company_profile):
        engine = MatchingEngine(sample_company_profile)
        tenders = [
            {'title': '项目A', 'budget': 500, 'qualifications': [], 'region': '广东省', 
             'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')},
            {'title': '项目B', 'budget': 800, 'qualifications': [], 'region': '北京市',
             'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')},
        ]
        top_matches = engine.get_top_matches(tenders, top_n=2)
        
        assert len(top_matches) <= 2
        assert all('tender' in m and 'match_result' in m for m in top_matches)

    def test_filter_by_recommendation(self, sample_company_profile, sample_tender_info):
        engine = MatchingEngine(sample_company_profile)
        results = engine.filter_by_recommendation(
            [sample_tender_info], 
            recommendations=['强烈推荐', '推荐']
        )
        assert isinstance(results, list)
