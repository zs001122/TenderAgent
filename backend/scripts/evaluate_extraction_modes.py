#!/usr/bin/env python3
"""
抽取模式评估脚本：对比 Rule / Agent 的字段覆盖率与耗时。

示例：
  python backend/scripts/evaluate_extraction_modes.py --sample-size 20 --mode both
  python backend/scripts/evaluate_extraction_modes.py --tender-ids 105,106,107 --mode both
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


def _bootstrap_path() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


@dataclass
class ModeEval:
    mode: str
    tender_id: int
    success: bool
    duration_ms: int
    error_count: int
    warning_count: int
    errors: List[str]
    fields: Dict[str, bool]


FIELD_KEYS = [
    "budget",
    "deadline",
    "qualifications",
    "contact",
    "tags",
    "region",
    "project_type",
]


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _extract_field_presence(info: Any) -> Dict[str, bool]:
    budget = bool(getattr(getattr(info, "budget", None), "value", None) is not None)
    deadline = bool(getattr(getattr(info, "deadline", None), "value", None) is not None)
    qualifications = bool(getattr(getattr(info, "qualifications", None), "required", None))
    contact_obj = getattr(info, "contact", None)
    contact = any([
        _has_text(getattr(contact_obj, "person", "")),
        _has_text(getattr(contact_obj, "phone", "")),
        _has_text(getattr(contact_obj, "email", "")),
    ])
    tags = bool(getattr(info, "tags", None))
    region = _has_text(getattr(info, "region", ""))
    project_type = _has_text(getattr(info, "project_type", ""))
    return {
        "budget": budget,
        "deadline": deadline,
        "qualifications": qualifications,
        "contact": contact,
        "tags": tags,
        "region": region,
        "project_type": project_type,
    }


def _evaluate_one(mode: str, tender: Any, rule_pipeline: Any, agent_service: Any, agent_timeout: int) -> ModeEval:
    started = time.perf_counter()
    if mode == "rule":
        result = rule_pipeline.extract(tender.content or "")
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(agent_service.extract, tender.content or "", tender.title or "")
            try:
                result = future.result(timeout=max(agent_timeout + 2, 3))
            except FutureTimeoutError:
                duration_ms = int((time.perf_counter() - started) * 1000)
                return ModeEval(
                    mode=mode,
                    tender_id=int(tender.id),
                    success=False,
                    duration_ms=duration_ms,
                    error_count=1,
                    warning_count=0,
                    errors=[f"agent_timeout>{agent_timeout}s"],
                    fields={k: False for k in FIELD_KEYS},
                )
    duration_ms = int((time.perf_counter() - started) * 1000)
    fields = _extract_field_presence(result.info)
    return ModeEval(
        mode=mode,
        tender_id=int(tender.id),
        success=bool(result.success),
        duration_ms=duration_ms,
        error_count=len(result.errors or []),
        warning_count=len(result.warnings or []),
        errors=[str(x) for x in (result.errors or [])],
        fields=fields,
    )


def _aggregate(items: List[ModeEval]) -> Dict[str, Any]:
    total = len(items)
    if total == 0:
        return {
            "total": 0,
            "success_rate": 0.0,
            "avg_duration_ms": 0.0,
            "avg_error_count": 0.0,
            "field_fill_rates": {k: 0.0 for k in FIELD_KEYS},
            "overall_fill_rate": 0.0,
        }
    success_count = sum(1 for x in items if x.success)
    avg_duration_ms = round(sum(x.duration_ms for x in items) / total, 2)
    avg_error_count = round(sum(x.error_count for x in items) / total, 2)
    error_counter: Counter[str] = Counter()
    for item in items:
        for err in item.errors:
            if err:
                error_counter[err] += 1

    field_fill_rates: Dict[str, float] = {}
    field_true_total = 0
    for key in FIELD_KEYS:
        c = sum(1 for x in items if x.fields.get(key, False))
        field_fill_rates[key] = round(c / total, 4)
        field_true_total += c
    overall_fill_rate = round(field_true_total / (total * len(FIELD_KEYS)), 4)

    return {
        "total": total,
        "success_rate": round(success_count / total, 4),
        "avg_duration_ms": avg_duration_ms,
        "avg_error_count": avg_error_count,
        "field_fill_rates": field_fill_rates,
        "overall_fill_rate": overall_fill_rate,
        "top_errors": [
            {"error": msg, "count": cnt}
            for msg, cnt in error_counter.most_common(5)
        ],
    }


def _pick_tenders(session: Any, sample_size: int, tender_ids: List[int]) -> List[Any]:
    from sqlmodel import select
    from app.models.tender import Tender

    if tender_ids:
        rows = []
        for tid in tender_ids:
            item = session.get(Tender, tid)
            if item and (item.content or "").strip():
                rows.append(item)
        return rows

    rows = session.exec(
        select(Tender)
        .where(Tender.content.is_not(None))
        .order_by(Tender.publish_date.desc())
        .limit(max(sample_size * 4, sample_size))
    ).all()
    rows = [x for x in rows if (x.content or "").strip()]
    if len(rows) > sample_size:
        random.seed(42)
        rows = random.sample(rows, sample_size)
    return rows


def _compare(rule_stats: Dict[str, Any], agent_stats: Dict[str, Any]) -> Dict[str, Any]:
    delta_fields = {
        key: round(agent_stats["field_fill_rates"][key] - rule_stats["field_fill_rates"][key], 4)
        for key in FIELD_KEYS
    }
    return {
        "overall_fill_rate_delta": round(agent_stats["overall_fill_rate"] - rule_stats["overall_fill_rate"], 4),
        "avg_duration_ms_delta": round(agent_stats["avg_duration_ms"] - rule_stats["avg_duration_ms"], 2),
        "success_rate_delta": round(agent_stats["success_rate"] - rule_stats["success_rate"], 4),
        "field_fill_rate_delta": delta_fields,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--tender-ids", type=str, default="")
    parser.add_argument("--mode", choices=["rule", "agent", "both"], default="both")
    parser.add_argument("--agent-timeout", type=int, default=15)
    parser.add_argument("--output-json", type=str, default="")
    args = parser.parse_args()

    _bootstrap_path()

    from sqlmodel import Session
    from app.db.session import engine
    from app.services.extraction.pipeline import InformationFusionPipeline
    from app.services.extraction.agent_extractor import AgentExtractionService

    tender_ids = [int(x) for x in args.tender_ids.split(",") if x.strip().isdigit()]
    with Session(engine) as session:
        tenders = _pick_tenders(session, sample_size=max(args.sample_size, 1), tender_ids=tender_ids)

    if not tenders:
        print("no_tenders_available")
        return 1

    rule_pipeline = InformationFusionPipeline()
    agent_service = AgentExtractionService()
    agent_service.timeout_seconds = max(args.agent_timeout, 1)

    mode_results: Dict[str, List[ModeEval]] = {"rule": [], "agent": []}
    run_modes = ["rule", "agent"] if args.mode == "both" else [args.mode]

    for tender in tenders:
        for mode in run_modes:
            mode_results[mode].append(_evaluate_one(mode, tender, rule_pipeline, agent_service, args.agent_timeout))

    output: Dict[str, Any] = {
        "sample_tender_ids": [int(t.id) for t in tenders],
        "sample_size": len(tenders),
        "mode": args.mode,
        "agent_timeout_seconds": agent_service.timeout_seconds,
    }

    if "rule" in run_modes:
        output["rule"] = _aggregate(mode_results["rule"])
    if "agent" in run_modes:
        output["agent"] = _aggregate(mode_results["agent"])
    if args.mode == "both":
        output["compare"] = _compare(output["rule"], output["agent"])

    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.output_json:
        p = Path(args.output_json)
        p.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved={p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
