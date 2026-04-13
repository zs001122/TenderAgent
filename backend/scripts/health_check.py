import sys
import json
from pathlib import Path


def _build_crawler_metrics(root: Path) -> dict:
    backend_dir = root / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from sqlmodel import Session  # type: ignore
    from app.db.session import engine  # type: ignore
    from app.db.repository import TenderRepository  # type: ignore

    with Session(engine) as session:
        repo = TenderRepository(session)
        return repo.get_crawler_health_stats(hours=24)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "backend" / "app" / "main.py",
        root / "backend" / "app" / "db" / "session.py",
        root / "frontend" / "package.json",
        root / "memory.md",
        root / ".trae" / "documents" / "tender_system_implementation_plan.md",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("health_check_failed")
        for item in missing:
            print(item)
        return 1
    print("health_check_ok")
    try:
        metrics = _build_crawler_metrics(root)
        print(json.dumps({"crawler_health": metrics}, ensure_ascii=False))
    except Exception as exc:
        print(f"crawler_health_collect_failed: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
