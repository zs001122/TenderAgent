import pytest
from datetime import datetime

from app.services.extraction.pipeline import InformationFusionPipeline, get_extraction_pipeline
from app.services.extraction.rough_extractor import RoughExtractor


class TestRoughExtractor:
    """粗抽模块测试"""

    def setup_method(self):
        self.extractor = RoughExtractor()

    def test_extract_budget_wan(self):
        content = "采购预算：580万元"
        result = self.extractor.extract(content)
        assert len(result['budget']) > 0
        assert result['budget'][0]['value'] == 580.0
        assert result['budget'][0]['unit'] == '万元'

    def test_extract_budget_yuan(self):
        content = "项目金额：5,800,000元"
        result = self.extractor.extract(content)
        assert len(result['budget']) > 0
        assert result['budget'][0]['value'] == 580.0

    def test_extract_deadline(self):
        content = "投标截止时间：2026年4月15日17:00"
        result = self.extractor.extract(content)
        assert len(result['deadline']) > 0
        assert result['deadline'][0]['value'].year == 2026

    def test_extract_qualifications(self):
        content = "投标人须具备CMMI3级资质，具有ISO27001认证"
        result = self.extractor.extract(content)
        assert len(result['qualifications']['required']) > 0

    def test_extract_contact(self):
        content = "联系人：张经理，联系电话：0755-12345678，邮箱：test@example.com"
        result = self.extractor.extract(content)
        assert '张经理' in result['contact']['person']
        assert result['contact']['email'] == 'test@example.com'

    def test_extract_keywords(self):
        content = "本项目涉及大数据平台开发和AI智能分析"
        result = self.extractor.extract(content)
        assert '大数据' in result['tags'] or 'AI/人工智能' in result['tags']

    def test_extract_empty_content(self):
        result = self.extractor.extract("")
        assert result['budget'] == []


class TestInformationFusionPipeline:
    """信息融合管道集成测试"""

    def setup_method(self):
        self.pipeline = InformationFusionPipeline()

    def test_extract_full_content(self, sample_tender_content):
        result = self.pipeline.extract(sample_tender_content)
        assert result.success == True
        assert result.info.budget.value == 580.0

    def test_extract_empty_content(self):
        result = self.pipeline.extract("")
        assert result.success == False

    def test_quick_extract(self, sample_tender_content):
        quick_result = self.pipeline.quick_extract(sample_tender_content)
        assert 'budget' in quick_result
        assert 'deadline' in quick_result

    def test_extract_batch(self):
        items = [
            {'content': '采购预算：100万元，截止时间：2026年5月1日'},
            {'content': '项目金额：200万元，投标截止：2026年6月1日'},
        ]
        results = self.pipeline.extract_batch(items)
        assert len(results) == 2

    def test_get_extraction_pipeline_singleton(self):
        pipeline1 = get_extraction_pipeline()
        pipeline2 = get_extraction_pipeline()
        assert pipeline1 is pipeline2
