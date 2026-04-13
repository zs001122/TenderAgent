from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.api import api_router
from app.db.session import init_db, engine
from sqlmodel import Session


app = FastAPI(
    title="招标商机挖掘系统 API",
    description="抓取 → 提取 → 匹配 → 推荐 完整流程",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        from app.db.repository import TenderRepository
        repo = TenderRepository(session)
        count = repo.count_tenders()
        print(f"数据库初始化完成，当前招标数量: {count}")


@app.get("/")
def root():
    return {
        "message": "招标商机挖掘系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "tenders": "/api/tenders/",
            "analysis": "/api/analysis/",
            "dashboard": "/api/dashboard/",
            "company": "/api/company/",
            "feedback": "/api/feedback/",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
