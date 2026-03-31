from typing import List, Optional, Dict, Set


class QualificationMapping:
    """资质映射图谱 - 轻量级
    
    提供资质名称的标准化和等价判断
    """
    
    EQUIVALENT_QUALIFICATIONS: Dict[str, List[str]] = {
        'ISO27001': [
            'ISO27001', 'ISO/IEC 27001', 'ISO 27001',
            '信息安全管理体系认证', '信息安全管理体系', 'ISO27001认证'
        ],
        'ISO9001': [
            'ISO9001', 'ISO 9001', 'ISO/IEC 9001',
            '质量管理体系认证', '质量管理体系', 'ISO9001认证'
        ],
        'ISO20000': [
            'ISO20000', 'ISO 20000', 'ISO/IEC 20000',
            'IT服务管理体系认证', 'IT服务管理体系'
        ],
        'CMMI3': [
            'CMMI3', 'CMMI三级', 'CMMI-ML3', 'CMMI L3',
            'CMMI Level 3', '能力成熟度模型集成三级', 'CMMI3级'
        ],
        'CMMI5': [
            'CMMI5', 'CMMI五级', 'CMMI-ML5', 'CMMI L5',
            'CMMI Level 5', '能力成熟度模型集成五级', 'CMMI5级'
        ],
        '等保三级': [
            '等保三级', '信息安全等级保护三级', '三级等保',
            '等保三级认证', '等级保护三级'
        ],
        '等保二级': [
            '等保二级', '信息安全等级保护二级', '二级等保',
            '等保二级认证', '等级保护二级'
        ],
        '高新技术企业': [
            '高新技术企业', '高新企业', '国家高新技术企业',
            '高新技术企业认证', '高新认证'
        ],
        'ITSS': [
            'ITSS', 'ITSS认证', '信息技术服务标准',
            'IT服务标准认证'
        ],
        'CS': [
            'CS', 'CS认证', '信息系统建设和服务能力认证',
            '信息系统建设能力'
        ],
        'CCRC': [
            'CCRC', 'CCRC认证', '信息安全服务资质',
            '信息安全服务认证'
        ],
    }
    
    QUALIFICATION_CATEGORIES: Dict[str, str] = {
        'ISO27001': '安全认证',
        'ISO9001': '质量认证',
        'ISO20000': '服务认证',
        'CMMI3': '能力认证',
        'CMMI5': '能力认证',
        '等保三级': '安全认证',
        '等保二级': '安全认证',
        '高新技术企业': '企业资质',
        'ITSS': '服务认证',
        'CS': '能力认证',
        'CCRC': '安全认证',
    }
    
    _reverse_index: Dict[str, str] = {}
    
    @classmethod
    def _build_reverse_index(cls):
        """构建反向索引"""
        if cls._reverse_index:
            return
        
        for standard, aliases in cls.EQUIVALENT_QUALIFICATIONS.items():
            for alias in aliases:
                cls._reverse_index[alias.lower()] = standard
    
    @classmethod
    def normalize(cls, qual_name: str) -> str:
        """标准化资质名称
        
        Args:
            qual_name: 原始资质名称
        
        Returns:
            标准化后的资质名称
        """
        if not qual_name:
            return ""
        
        cls._build_reverse_index()
        
        qual_lower = qual_name.strip().lower()
        
        if qual_lower in cls._reverse_index:
            return cls._reverse_index[qual_lower]
        
        for standard, aliases in cls.EQUIVALENT_QUALIFICATIONS.items():
            for alias in aliases:
                if alias.lower() in qual_lower or qual_lower in alias.lower():
                    return standard
        
        return qual_name.strip()
    
    @classmethod
    def is_equivalent(cls, qual1: str, qual2: str) -> bool:
        """判断两个资质是否等价
        
        Args:
            qual1: 资质名称1
            qual2: 资质名称2
        
        Returns:
            是否等价
        """
        return cls.normalize(qual1) == cls.normalize(qual2)
    
    @classmethod
    def get_aliases(cls, qual_name: str) -> List[str]:
        """获取资质的所有别名
        
        Args:
            qual_name: 资质名称
        
        Returns:
            别名列表
        """
        standard = cls.normalize(qual_name)
        return cls.EQUIVALENT_QUALIFICATIONS.get(standard, [standard])
    
    @classmethod
    def get_category(cls, qual_name: str) -> str:
        """获取资质类别
        
        Args:
            qual_name: 资质名称
        
        Returns:
            资质类别
        """
        standard = cls.normalize(qual_name)
        return cls.QUALIFICATION_CATEGORIES.get(standard, '其他')
    
    @classmethod
    def find_matching_qualifications(
        cls, 
        required: str, 
        owned: List[str]
    ) -> List[str]:
        """在已有资质中找到匹配的资质
        
        Args:
            required: 要求的资质
            owned: 已有的资质列表
        
        Returns:
            匹配的资质列表
        """
        matches = []
        required_standard = cls.normalize(required)
        
        for qual in owned:
            if cls.normalize(qual) == required_standard:
                matches.append(qual)
        
        return matches
    
    @classmethod
    def add_qualification(cls, standard: str, aliases: List[str], category: str = '其他'):
        """添加新的资质映射
        
        Args:
            standard: 标准名称
            aliases: 别名列表
            category: 资质类别
        """
        cls.EQUIVALENT_QUALIFICATIONS[standard] = aliases
        cls.QUALIFICATION_CATEGORIES[standard] = category
        cls._reverse_index.clear()
