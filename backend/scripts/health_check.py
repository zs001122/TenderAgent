import sys
from pathlib import Path


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
