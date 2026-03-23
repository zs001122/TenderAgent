from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.api import api_router
from app.db.repository import get_repository

app = FastAPI(title="Tender Opportunity Mining System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # Initialize repository
    repo = get_repository()
    print(f"Repository initialized with {repo.count_tenders()} tenders.")

@app.get("/")
def root():
    return {"message": "Welcome to Tender Opportunity Mining System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
