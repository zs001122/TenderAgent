import os
import sys
import logging
from datetime import datetime

# 确保后端目录在路径中，以便我们可以导入 app 模块
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from sqlmodel import Session, select
from app.db.session import engine
from app.models.tender import Tender, CrawlLog
from scrapers import ChinaTelecomScraper, ChinaMobileScraper

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(base_dir, "scraper.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainScraper")

def get_last_publish_date(session: Session, source_site: str) -> datetime:
    """获取指定来源站点的最近发布日期，用作增量边界。"""
    statement = select(Tender.publish_date).where(Tender.source_site == source_site).order_by(Tender.publish_date.desc()).limit(1)
    result = session.exec(statement).first()
    return result

def run_scrapers():
    scrapers = [
        # ChinaTelecomScraper(),
        ChinaMobileScraper()
    ]

    with Session(engine) as session:
        for scraper in scrapers:
            logger.info(f"Starting scraper for {scraper.name}")
            
            # 1. 初始化爬取日志
            log_entry = CrawlLog(
                source_site=scraper.name,
                start_time=datetime.now(),
                status="RUNNING"
            )
            session.add(log_entry)
            session.commit()
            
            # 2. 确定增量边界
            last_date = get_last_publish_date(session, scraper.name)
            logger.info(f"Incremental boundary for {scraper.name}: {last_date}")

            new_count = 0
            try:
                # 3. 运行爬虫
                # 出于演示目的，我们将 max_pages 限制为 2，以防止在测试期间运行过长
                for tender_data in scraper.run(max_pages=2, last_publish_date=last_date):
                    # 通过 URL 检查数据库中是否存在完全相同的记录
                    url = tender_data.get("source_url")
                    if not url:
                        continue
                        
                    existing = session.exec(select(Tender).where(Tender.source_url == url)).first()
                    if existing:
                        logger.debug(f"Tender already exists: {url}")
                        continue
                        
                    # 插入新的招标公告
                    new_tender = Tender(**tender_data)
                    session.add(new_tender)
                    new_count += 1
                    
                    # Commit in batches to avoid losing data if it crashes
                    if new_count % 10 == 0:
                        session.commit()
                        logger.info(f"Committed {new_count} new tenders for {scraper.name}...")

                # 最后提交剩余的项目
                session.commit()
                log_entry.status = "SUCCESS"
                
            except Exception as e:
                logger.error(f"Error running scraper {scraper.name}: {e}", exc_info=True)
                log_entry.status = "FAILED"
                session.rollback()
            finally:
                # 4. 完成日志记录
                log_entry.end_time = datetime.now()
                log_entry.new_count = new_count
                session.add(log_entry)
                session.commit()
                logger.info(f"Finished {scraper.name}. Added {new_count} new tenders. Status: {log_entry.status}")

if __name__ == "__main__":
    logger.info("Starting master scraper orchestrator...")
    run_scrapers()
    logger.info("Master scraper run completed.")
