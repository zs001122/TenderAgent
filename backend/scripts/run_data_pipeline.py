import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
backend_dir = os.path.join(project_root, "backend")
crawlers_dir = os.path.join(project_root, "crawlers")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if crawlers_dir not in sys.path:
    sys.path.insert(0, crawlers_dir)

from sqlmodel import Session
from app.db.session import engine
from app.services.pipeline_service import PipelineService
from main_scraper import run_scrapers


def run_once(max_pages: int, analyze_limit: int, scraper_targets, run_analysis: bool):
    started_at = datetime.now().isoformat()
    scrape_summary = run_scrapers(max_pages=max_pages, scraper_targets=scraper_targets)
    if scrape_summary.get("total_scrapers", 0) == 0:
        print("[pipeline] no available scraper, please install crawler dependencies if needed.")
        print("[pipeline] hint: pip install -r crawlers/requirements.txt && playwright install chromium")

    analysis_summary = {
        "total": 0,
        "processed": 0,
        "tender_ids": [],
    }
    if run_analysis:
        with Session(engine) as session:
            service = PipelineService(session)
            analysis_summary = service.process_unanalyzed(limit=analyze_limit)

    result = {
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(),
        "scrape": scrape_summary,
        "analysis": analysis_summary,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def seconds_until(target_hhmm: str) -> int:
    now = datetime.now()
    hour, minute = target_hhmm.split(":")
    target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return int((target - now).total_seconds())


def run_daemon(target_time: str, max_pages: int, analyze_limit: int, scraper_targets, run_analysis: bool):
    while True:
        wait_seconds = seconds_until(target_time)
        print(f"[pipeline] next run at {target_time}, waiting {wait_seconds}s")
        time.sleep(wait_seconds)
        try:
            run_once(
                max_pages=max_pages,
                analyze_limit=analyze_limit,
                scraper_targets=scraper_targets,
                run_analysis=run_analysis,
            )
        except Exception as exc:
            print(f"[pipeline] run failed: {exc}")


def parse_targets(raw_targets: str):
    if not raw_targets:
        return None
    return [item.strip() for item in raw_targets.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["once", "daemon"], default="once")
    parser.add_argument("--time", default="02:00")
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--analyze-limit", type=int, default=200)
    parser.add_argument("--scrapers", default="cmcc,telecom")
    parser.add_argument("--skip-analysis", action="store_true")
    args = parser.parse_args()

    targets = parse_targets(args.scrapers)
    run_analysis = not args.skip_analysis
    if args.mode == "once":
        run_once(
            max_pages=args.max_pages,
            analyze_limit=args.analyze_limit,
            scraper_targets=targets,
            run_analysis=run_analysis,
        )
        return
    run_daemon(
        target_time=args.time,
        max_pages=args.max_pages,
        analyze_limit=args.analyze_limit,
        scraper_targets=targets,
        run_analysis=run_analysis,
    )


if __name__ == "__main__":
    main()
