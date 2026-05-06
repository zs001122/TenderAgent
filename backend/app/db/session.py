from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text
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
    from app.models.company import CompanyProfile, CompanyAsset
    from app.models.feedback import BidRecord, FeedbackAnalysis
    from app.models.analysis_trace import AnalysisTrace
    
    SQLModel.metadata.create_all(engine)
    _ensure_compat_columns()


def _ensure_compat_columns():
    """Add lightweight compatibility columns for existing SQLite databases."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.begin() as connection:
        if "analysis_results" in table_names:
            columns = {column["name"] for column in inspector.get_columns("analysis_results")}
            if "matching_details" not in columns:
                connection.execute(text("ALTER TABLE analysis_results ADD COLUMN matching_details TEXT"))

        if "company_assets" in table_names:
            columns = {column["name"] for column in inspector.get_columns("company_assets")}
            if "source_type" not in columns:
                connection.execute(text("ALTER TABLE company_assets ADD COLUMN source_type VARCHAR DEFAULT 'excel_import'"))
            if "is_deleted" not in columns:
                connection.execute(text("ALTER TABLE company_assets ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
            if "deleted_at" not in columns:
                connection.execute(text("ALTER TABLE company_assets ADD COLUMN deleted_at DATETIME"))
            if "deleted_reason" not in columns:
                connection.execute(text("ALTER TABLE company_assets ADD COLUMN deleted_reason VARCHAR"))


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def init_db():
    """初始化数据库"""
    create_db_and_tables()
