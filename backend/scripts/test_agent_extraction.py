#!/usr/bin/env python3
"""
Agent 抽取链路排障脚本。

用法：
  python backend/scripts/test_agent_extraction.py --tender-id 105
  python backend/scripts/test_agent_extraction.py --skip-pipeline
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict


def _bootstrap_path() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def _mask_key(key: str) -> str:
    if not key:
        return "<EMPTY>"
    if len(key) <= 10:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


def _resolve_model(raw_model: str) -> str:
    return raw_model if "/" in raw_model else f"openai/{raw_model}"


def _normalize_api_base(value: str) -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return raw
    if raw.endswith("/chat/completions"):
        return raw[: -len("/chat/completions")]
    return raw


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _test_litellm(settings: Any, timeout: int) -> Dict[str, Any]:
    _print_section("Step 1: LiteLLM Connectivity")
    try:
        from litellm import completion
    except Exception as exc:
        return {"ok": False, "error": f"litellm import failed: {exc}"}

    model = _resolve_model(settings.LLM_MODEL)
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": "reply with: ok"}],
        "temperature": 0,
        "max_tokens": 10,
        "timeout": timeout,
    }
    if settings.LLM_API_KEY:
        kwargs["api_key"] = settings.LLM_API_KEY
    if settings.LLM_BASE_URL:
        kwargs["api_base"] = _normalize_api_base(settings.LLM_BASE_URL)

    try:
        resp = completion(**kwargs)
        text = (resp.choices[0].message.content or "").strip()
        print(f"model={model}")
        print(f"response={text!r}")
        return {"ok": True, "response": text}
    except Exception as exc:
        print(f"model={model}")
        print(f"error={exc}")
        return {"ok": False, "error": str(exc)}


def _test_pipeline_debug(tender_id: int) -> Dict[str, Any]:
    _print_section("Step 2: Pipeline Debug Extraction")
    from sqlmodel import Session
    from app.db.session import engine
    from app.services.pipeline_service import PipelineService

    with Session(engine) as session:
        svc = PipelineService(session)
        result = svc.debug_extraction(tender_id)
    if not result:
        print(f"tender_id={tender_id} not found")
        return {"ok": False, "error": "tender not found"}

    print(f"configured_mode={result.get('configured_mode')}")
    print(f"selected_mode={result.get('selected_mode')}")
    print(f"fallback_used={result.get('fallback_used')}")
    print(f"success={result.get('success')}")
    print(f"errors={result.get('errors')}")
    print(f"warnings={result.get('warnings')}")
    return {"ok": True, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tender-id", type=int, default=105)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--skip-pipeline", action="store_true")
    args = parser.parse_args()

    _bootstrap_path()

    from app.core.config import settings

    _print_section("Config Snapshot")
    print(f"LLM_API_KEY={_mask_key(settings.LLM_API_KEY)}")
    print(f"LLM_BASE_URL={settings.LLM_BASE_URL}")
    print(f"LLM_MODEL={settings.LLM_MODEL}")
    print(f"EXTRACTION_MODE={settings.EXTRACTION_MODE}")

    litellm_result = _test_litellm(settings, timeout=args.timeout)
    if not args.skip_pipeline:
        _test_pipeline_debug(args.tender_id)

    _print_section("Summary")
    if litellm_result.get("ok"):
        print("litellm: OK")
    else:
        print("litellm: FAIL")
        print(f"reason: {litellm_result.get('error')}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
