import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlmodel import Session, SQLModel, create_engine
from app.models.tender import Tender
from app.models.company import CompanyProfile
from app.db.session import engine

def create_test_data():
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # 创建测试招标数据
        tenders_data = [
            {
                "title": "某省政府大数据平台建设项目招标公告",
                "source_url": "https://example.com/tender/001",
                "source_site": "政府采购网",
                "notice_type": "公开招标",
                "content": """
项目名称：某省政府大数据平台建设项目
预算金额：500万元
投标截止日期：2026-04-15
资质要求：CMMI3以上、高新技术企业
项目概述：建设省级大数据处理平台，包含数据采集、存储、分析等功能。
联系人：张先生
联系电话：010-12345678
                """,
                "region": "广东省",
                "budget_amount": 500.0,
                "publish_date": datetime.now() - timedelta(days=2),
            },
            {
                "title": "智慧城市AI视频分析系统采购项目",
                "source_url": "https://example.com/tender/002",
                "source_site": "招标网",
                "notice_type": "公开招标",
                "content": """
项目名称：智慧城市AI视频分析系统采购
预算金额：800万元
投标截止日期：2026-04-20
资质要求：ISO27001、具备AI项目实施经验
项目概述：建设城市级视频AI分析系统，支持人脸识别、行为分析等功能。
联系人：李女士
联系电话：021-87654321
                """,
                "region": "上海市",
                "budget_amount": 800.0,
                "publish_date": datetime.now() - timedelta(days=3),
            },
            {
                "title": "企业ERP系统开发服务招标",
                "source_url": "https://example.com/tender/003",
                "source_site": "企业采购网",
                "notice_type": "邀请招标",
                "content": """
项目名称：企业ERP系统开发服务
预算金额：150万元
投标截止日期：2026-04-10
资质要求：软件开发相关资质
项目概述：开发企业内部ERP系统，包含财务、采购、库存模块。
联系人：王先生
联系电话：0755-11112222
                """,
                "region": "广东省",
                "budget_amount": 150.0,
                "publish_date": datetime.now() - timedelta(days=1),
            },
            {
                "title": "医院信息化系统升级改造项目",
                "source_url": "https://example.com/tender/004",
                "source_site": "医疗采购网",
                "notice_type": "公开招标",
                "content": """
项目名称：医院信息化系统升级改造
预算金额：1200万元
投标截止日期：2026-05-01
资质要求：CMMI5、医疗信息化资质
项目概述：升级改造医院HIS、LIS、PACS等信息系统。
联系人：赵女士
联系电话：010-33334444
                """,
                "region": "北京市",
                "budget_amount": 1200.0,
                "publish_date": datetime.now() - timedelta(days=5),
            },
            {
                "title": "工业园区智能监控系统项目",
                "source_url": "https://example.com/tender/005",
                "source_site": "工程招标网",
                "notice_type": "公开招标",
                "content": """
项目名称：工业园区智能监控系统
预算金额：300万元
投标截止日期：2026-04-18
资质要求：安防资质、系统集成资质
项目概述：建设工业园区全覆盖智能监控系统。
联系人：陈先生
联系电话：020-55556666
                """,
                "region": "广东省",
                "budget_amount": 300.0,
                "publish_date": datetime.now() - timedelta(days=4),
            },
        ]
        
        for data in tenders_data:
            tender = Tender(**data)
            session.add(tender)
        
        # 创建公司画像
        company = CompanyProfile(
            name="天网智能科技",
            target_domains='["软件开发", "大数据", "AI/人工智能"]',
            budget_range_min=50,
            budget_range_max=2000,
            qualifications='["CMMI3", "ISO27001", "高新技术企业"]',
            service_regions='["广东省", "北京市", "上海市"]',
            is_active=True,
        )
        session.add(company)
        
        session.commit()
        print(f"成功创建 {len(tenders_data)} 条测试招标数据")

if __name__ == "__main__":
    create_test_data()