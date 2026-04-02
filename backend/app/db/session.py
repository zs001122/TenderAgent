from sqlmodel import SQLModel, create_engine, Session
import os

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(base_dir, "tender.db")
default_database_url = f"sqlite:///{db_path}"
DATABASE_URL = os.getenv("DATABASE_URL", default_database_url)
DB_ECHO = os.getenv("DB_ECHO", "false").strip().lower() in {"1", "true", "yes", "on"}

engine = create_engine(DATABASE_URL, echo=DB_ECHO)


def create_db_and_tables():
    """创建数据库表"""
    from app.models.tender import Tender, CrawlLog
    from app.models.analysis import AnalysisResult
    from app.models.company import CompanyProfile
    from app.models.feedback import BidRecord, FeedbackAnalysis
    
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def init_db():
    """初始化数据库"""
    create_db_and_tables()
