from sqlmodel import Field, SQLModel, create_engine
import os

# SQLite for now, can be switched to PostgreSQL later by changing this URL
# DATABASE_URL = "postgresql://user:password@localhost/dbname"
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
db_path = os.path.join(base_dir, "tender.db")
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session
