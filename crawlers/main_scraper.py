import os
import sys
import logging
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

crawlers_dir = os.path.dirname(os.path.abspath(__file__))
if crawlers_dir not in sys.path:
    sys.path.insert(0, crawlers_dir)

from sqlmodel import Session, select
from app.db.session import engine
from app.models.tender import Tender, CrawlLog
from scrapers import ChinaTelecomScraper, ChinaMobileScraper

logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "scraper.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainScraper")

def get_last_publish_date(session: Session, source_site: str) -> datetime:
    statement = select(Tender.publish_date).where(Tender.source_site == source_site).order_by(Tender.publish_date.desc()).limit(1)
    result = session.exec(statement).first()
    return result

def run_scrapers():
    scrapers = [
        ChinaMobileScraper(),
    ]

    with Session(engine) as session:
        for scraper in scrapers:
            logger.info(f"Starting scraper for {scraper.name}")
            
            log_entry = CrawlLog(
                source_site=scraper.name,
                start_time=datetime.now(),
                status="RUNNING"
            )
            session.add(log_entry)
            session.commit()
            
            last_date = get_last_publish_date(session, scraper.name)
            logger.info(f"Incremental boundary for {scraper.name}: {last_date}")

            new_count = 0
            try:
                for tender_data in scraper.run(max_pages=2, last_publish_date=last_date):
                    url = tender_data.get("source_url")
                    if not url:
                        continue
                        
                    existing = session.exec(select(Tender).where(Tender.source_url == url)).first()
                    if existing:
                        logger.debug(f"Tender already exists: {url}")
                        continue
                        
                    new_tender = Tender(**tender_data)
                    session.add(new_tender)
                    new_count += 1
                    
                    if new_count % 10 == 0:
                        session.commit()
                        logger.info(f"Committed {new_count} new tenders for {scraper.name}...")

                session.commit()
                log_entry.status = "SUCCESS"
                
            except Exception as e:
                logger.error(f"Error running scraper {scraper.name}: {e}", exc_info=True)
                log_entry.status = "FAILED"
                session.rollback()
            finally:
                log_entry.end_time = datetime.now()
                log_entry.new_count = new_count
                session.add(log_entry)
                session.commit()
                logger.info(f"Finished {scraper.name}. Added {new_count} new tenders. Status: {log_entry.status}")

if __name__ == "__main__":
    logger.info("Starting master scraper orchestrator...")
    run_scrapers()
    logger.info("Master scraper run completed.")
