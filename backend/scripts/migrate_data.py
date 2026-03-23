import pandas as pd
from sqlmodel import Session, select
from app.db.session import engine
from app.models.tender import Tender
from datetime import datetime
import os

def migrate_csv_to_db(csv_path: str):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    df = df.fillna("")
    
    with Session(engine) as session:
        count = 0
        for _, row in df.iterrows():
            try:
                # Check duplication
                url = str(row.get('详情页url', ''))
                # If URL is missing, use title+date as fallback unique key (not ideal but works for demo)
                if not url or url == 'nan':
                    url = f"manual_{row.get('标题')}_{row.get('发布时间')}"
                    
                existing = session.exec(select(Tender).where(Tender.source_url == url)).first()
                if existing:
                    continue

                # Parse date
                pub_date_str = str(row.get('发布时间', ''))
                pub_date = datetime.now()
                # Try common formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        pub_date = datetime.strptime(pub_date_str, fmt)
                        break
                    except:
                        pass

                tender = Tender(
                    source_url=url,
                    source_site="中国电信", # Default for now
                    title=str(row.get('标题', '')),
                    publish_date=pub_date,
                    content=str(row.get('公告内容', ''))[:5000], # Truncate for safety
                    notice_type=str(row.get('公告类型', '')),
                    region=str(row.get('省份', ''))
                )
                session.add(tender)
                count += 1
            except Exception as e:
                print(f"Error processing row: {e}")
        
        session.commit()
        print(f"Successfully migrated {count} tenders to database.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_dir, "data", "中国电信采购公告.csv")
    if not os.path.exists(csv_path):
        # Fallback for dev environment path
        csv_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "data", "中国电信采购公告.csv")
    print(f"Migrating from: {csv_path}")
    migrate_csv_to_db(csv_path)
