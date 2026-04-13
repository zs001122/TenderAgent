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

from main_scraper import run_scrapers


def run_once(max_pages: int, scraper_targets):
    started_at = datetime.now().isoformat()
    scrape_summary = run_scrapers(max_pages=max_pages, scraper_targets=scraper_targets)
    if scrape_summary.get("total_scrapers", 0) == 0:
        print("[pipeline] no available scraper, please install crawler dependencies if needed.")
        print("[pipeline] hint: pip install -r crawlers/requirements.txt && playwright install chromium")

    analysis_summary = {
        "mode": "manual_only",
        "message": "analysis is disabled in data pipeline, trigger manually via API/UI",
    }

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


def run_daemon(target_time: str, max_pages: int, scraper_targets):
    while True:
        wait_seconds = seconds_until(target_time)
        print(f"[pipeline] next run at {target_time}, waiting {wait_seconds}s")
        time.sleep(wait_seconds)
        try:
            run_once(
                max_pages=max_pages,
                scraper_targets=scraper_targets,
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
    parser.add_argument("--scrapers", default="cmcc,telecom")
    args = parser.parse_args()

    targets = parse_targets(args.scrapers)
    if args.mode == "once":
        run_once(
            max_pages=args.max_pages,
            scraper_targets=targets,
        )
        return
    run_daemon(
        target_time=args.time,
        max_pages=args.max_pages,
        scraper_targets=targets,
    )


if __name__ == "__main__":
    main()
