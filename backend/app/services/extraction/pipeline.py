from typing import List, Optional

from .rough_extractor import RoughExtractor
from .normalizer import FieldNormalizer
from .validator import ConsistencyValidator
from .models import ExtractedInfo, ExtractionResult


class InformationFusionPipeline:
    """信息融合管道 - 替代单次抽取
    
    三阶段处理流程：
    1. 粗抽（RoughExtractor）- Recall优先，允许脏数据
    2. 归一化（FieldNormalizer）- 标准化字段格式
    3. 交叉验证（ConsistencyValidator）- 检查数据一致性
    """
    
    def __init__(self):
        self.rough_extractor = RoughExtractor()
        self.normalizer = FieldNormalizer()
        self.validator = ConsistencyValidator()
    
    def extract(
        self, 
        content: str, 
        attachments: Optional[List[str]] = None
    ) -> ExtractionResult:
        """执行完整的信息提取流程
        
        Args:
            content: 招标公告正文内容
            attachments: 附件文件路径列表（可选）
        
        Returns:
            ExtractionResult: 包含提取信息和验证结果
        """
        if not content:
            return ExtractionResult(
                success=False,
                info=ExtractedInfo(),
                errors=["内容为空，无法提取信息"]
            )
        
        rough_info = self.rough_extractor.extract(content, attachments or [])
        
        normalized_info = self.normalizer.normalize(rough_info)
        
        result = self.validator.validate(normalized_info)
        
        return result
    
    def extract_batch(
        self, 
        items: List[dict]
    ) -> List[ExtractionResult]:
        """批量提取信息
        
        Args:
            items: 待提取的项目列表，每项包含 content 和可选的 attachments
        
        Returns:
            提取结果列表
        """
        results = []
        for item in items:
            content = item.get('content', '')
            attachments = item.get('attachments', [])
            result = self.extract(content, attachments)
            results.append(result)
        return results
    
    def quick_extract(self, content: str) -> dict:
        """快速提取 - 仅返回关键字段
        
        用于需要快速预览的场景
        """
        result = self.extract(content)
        
        return {
            'budget': result.info.budget.value if result.info.budget else None,
            'budget_confidence': result.info.budget.confidence if result.info.budget else 0,
            'deadline': result.info.deadline.value.strftime('%Y-%m-%d') if result.info.deadline and result.info.deadline.value else None,
            'qualifications': result.info.qualifications.required if result.info.qualifications else [],
            'tags': result.info.tags,
            'region': result.info.region,
            'is_reliable': result.info.is_reliable,
            'issues': result.errors
        }


_pipeline_instance = None


def get_extraction_pipeline() -> InformationFusionPipeline:
    """获取全局 Pipeline 实例"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = InformationFusionPipeline()
    return _pipeline_instance
