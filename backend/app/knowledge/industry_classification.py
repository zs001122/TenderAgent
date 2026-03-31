from typing import Dict, List, Optional, Any


class IndustryClassification:
    """行业分类图谱 - 轻量级
    
    提供行业分类和关键词映射
    """
    
    INDUSTRY_TREE: Dict[str, Dict[str, List[str]]] = {
        'IT服务': {
            '软件开发': [
                'APP开发', '系统开发', '平台建设', '信息化建设',
                '软件定制', '应用开发', '系统建设'
            ],
            '大数据': [
                '数据清洗', '数据分析', '数据仓库', '数据治理',
                '数据平台', '数据中台', '大数据平台'
            ],
            'AI/人工智能': [
                '机器学习', 'NLP', '图像识别', '大模型',
                '深度学习', '智能算法', 'AI应用', '人工智能'
            ],
            '云计算': [
                '云平台', '云服务', '云迁移', '云运维',
                '私有云', '公有云', '混合云'
            ],
            '网络安全': [
                '安全服务', '安全运维', '渗透测试', '安全评估',
                '安全加固', '安全咨询'
            ],
        },
        '通信服务': {
            '基站建设': [
                '5G基站', '4G基站', '基站建设', '基站维护'
            ],
            '网络优化': [
                '网络覆盖', '信号优化', '网络质量', '网络优化'
            ],
            '传输网络': [
                '光缆', '传输网', '光纤', '传输设备'
            ],
        },
        '工程服务': {
            '机电工程': [
                '机电安装', '弱电工程', '智能化工程'
            ],
            '装修工程': [
                '室内装修', '办公装修', '装修改造'
            ],
        },
        '运维服务': {
            'IT运维': [
                '运维服务', '驻场运维', '技术支持', '系统运维'
            ],
            '设备维护': [
                '设备维保', '设备维护', '硬件维护'
            ],
        },
    }
    
    _keyword_index: Dict[str, str] = {}
    _sub_category_index: Dict[str, str] = {}
    
    @classmethod
    def _build_indexes(cls):
        """构建索引"""
        if cls._keyword_index:
            return
        
        for industry, sub_categories in cls.INDUSTRY_TREE.items():
            for sub_category, keywords in sub_categories.items():
                cls._sub_category_index[sub_category] = industry
                for keyword in keywords:
                    cls._keyword_index[keyword.lower()] = sub_category
    
    @classmethod
    def get_industry(cls, keyword: str) -> Optional[str]:
        """根据关键词获取所属行业
        
        Args:
            keyword: 关键词
        
        Returns:
            行业名称
        """
        cls._build_indexes()
        
        keyword_lower = keyword.lower()
        
        if keyword_lower in cls._keyword_index:
            sub_category = cls._keyword_index[keyword_lower]
            return cls._sub_category_index.get(sub_category)
        
        return None
    
    @classmethod
    def get_sub_category(cls, keyword: str) -> Optional[str]:
        """根据关键词获取子类别
        
        Args:
            keyword: 关键词
        
        Returns:
            子类别名称
        """
        cls._build_indexes()
        
        return cls._keyword_index.get(keyword.lower())
    
    @classmethod
    def get_full_path(cls, keyword: str) -> Optional[str]:
        """获取关键词的完整分类路径
        
        Args:
            keyword: 关键词
        
        Returns:
            完整路径，如 "IT服务/软件开发"
        """
        cls._build_indexes()
        
        keyword_lower = keyword.lower()
        
        if keyword_lower in cls._keyword_index:
            sub_category = cls._keyword_index[keyword_lower]
            industry = cls._sub_category_index.get(sub_category, '')
            return f"{industry}/{sub_category}"
        
        return None
    
    @classmethod
    def get_keywords_by_industry(cls, industry: str) -> List[str]:
        """获取某行业的所有关键词
        
        Args:
            industry: 行业名称
        
        Returns:
            关键词列表
        """
        keywords = []
        
        if industry in cls.INDUSTRY_TREE:
            for sub_category, kw_list in cls.INDUSTRY_TREE[industry].items():
                keywords.extend(kw_list)
        
        return keywords
    
    @classmethod
    def get_sub_categories(cls, industry: str) -> List[str]:
        """获取某行业的所有子类别
        
        Args:
            industry: 行业名称
        
        Returns:
            子类别列表
        """
        if industry in cls.INDUSTRY_TREE:
            return list(cls.INDUSTRY_TREE[industry].keys())
        return []
    
    @classmethod
    def classify_keywords(cls, keywords: List[str]) -> Dict[str, List[str]]:
        """对关键词列表进行分类
        
        Args:
            keywords: 关键词列表
        
        Returns:
            分类结果，key为行业，value为匹配的关键词
        """
        result: Dict[str, List[str]] = {}
        
        for keyword in keywords:
            industry = cls.get_industry(keyword)
            if industry:
                if industry not in result:
                    result[industry] = []
                result[industry].append(keyword)
        
        return result
    
    @classmethod
    def add_industry(cls, industry: str, sub_categories: Dict[str, List[str]]):
        """添加新的行业分类
        
        Args:
            industry: 行业名称
            sub_categories: 子类别及其关键词
        """
        cls.INDUSTRY_TREE[industry] = sub_categories
        cls._keyword_index.clear()
        cls._sub_category_index.clear()
