# Tender Opportunity Mining System

## Architecture
This project is split into several components:
- **Backend**: FastAPI (Python) - Serves API and handles analysis logic.
- **Frontend**: React + Vite + TailwindCSS - Web interface for viewing tenders and analysis.
- **Scripts**: Standalone Python scripts for data scraping and offline analysis.

## Directory Structure
```
/home/wushuxin/TenderAgent/
├── backend/                # Backend Code (FastAPI)
│   ├── app/
│   │   ├── main.py         # API Entry Point
│   │   └── services/       # Business Logic
├── frontend/               # Frontend Code (React)
├── data/                   # Data Files
│   ├── 中国电信采购公告.csv  # Main Data Source
│   └── analysis_results.json # Analysis Output
├── scripts/                # Utility Scripts
│   ├── scrapers/           # Data Collectors
│   │   ├── chinatelecom_playwright_scraper.py
│   │   └── api_scraper.py
│   ├── utils/              # Helper Scripts
│   └── tender_analysis_demo.py # Offline Analysis Runner
├── legacy/                 # Deprecated Scripts
├── docs/                   # Documentation
└── venv/                   # Python Virtual Environment
```

## How to Run

### 1. Web Application (Recommended)

**Start Backend:**
```bash
cd backend
../venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```
Access the dashboard at `http://localhost:5173`.

### 2. Standalone Scripts

**Run Scraper:**
```bash
cd scripts/scrapers
../../venv/bin/python chinatelecom_playwright_scraper.py
```

**Run Offline Analysis:**
```bash
cd scripts
../venv/bin/python tender_analysis_demo.py
```

## Features
- **Tender List**: View all tenders from the CSV file.
- **Detail View**: See full details of a selected tender.
- **AI Analysis**: Trigger LLM analysis for specific tenders.
- **Real-time Results**: View match scores, risk assessment, and competitor analysis.
