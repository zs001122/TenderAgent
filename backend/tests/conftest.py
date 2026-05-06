import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_tender_content():
    return """
    某市大数据平台建设项目招标公告
    
    一、项目概况
    项目名称：某市大数据平台建设项目
    采购预算：580万元
    项目地点：广东省深圳市
    
    二、投标人资格要求
    1. 投标人须具备CMMI3级及以上资质
    2. 具有ISO27001信息安全管理体系认证
    3. 高新技术企业优先
    
    三、投标截止时间
    投标截止时间：2026年6月15日17:00
    开标时间：2026年6月16日9:00
    
    四、联系方式
    联系人：张经理
    联系电话：0755-12345678
    邮箱：zhangsan@example.com
    
    五、项目内容
    本项目主要建设内容包括：大数据平台开发、数据治理、AI智能分析模块等。
    """


@pytest.fixture
def sample_company_profile():
    return {
        'name': '测试科技有限公司',
        'target_domains': ['软件开发', '大数据', 'AI/人工智能'],
        'budget_range': [50, 1000],
        'qualifications': ['CMMI3', 'ISO27001', '高新技术企业'],
        'service_regions': ['广东省', '北京市', '上海市'],
        'bid_history': [
            {'project': '某省大数据平台', 'won': True, 'budget': 500},
            {'project': '某市AI系统', 'won': True, 'budget': 300},
            {'project': '某区数据治理', 'won': False, 'budget': 200},
        ]
    }


@pytest.fixture
def sample_tender_info():
    return {
        'title': '某市大数据平台建设项目',
        'budget': 580,
        'deadline': '2026-06-15',
        'region': '广东省深圳市',
        'qualifications': ['CMMI3', 'ISO27001'],
        'project_type': '软件开发',
        'tags': ['大数据', 'AI/人工智能'],
        'content': '大数据平台开发、数据治理、AI智能分析'
    }
