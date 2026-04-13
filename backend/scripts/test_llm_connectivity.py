#!/usr/bin/env python3
"""
LLM 连通性测试脚本（仅连通，不走业务逻辑）。

示例：
  python backend/scripts/test_llm_connectivity.py
  python backend/scripts/test_llm_connectivity.py --model openai/gpt-4o-mini --timeout 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict


def _bootstrap() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def _mask_key(key: str) -> str:
    if not key:
        return "<EMPTY>"
    if len(key) < 12:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


def _resolve_model(model: str) -> str:
    return model if "/" in model else f"openai/{model}"


def _normalize_api_base(api_base: str) -> str:
    raw = str(api_base or "").strip().rstrip("/")
    if not raw:
        return raw
    if raw.endswith("/chat/completions"):
        return raw[: -len("/chat/completions")]
    return raw


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_test(model: str, api_key: str, api_base: str, timeout: int) -> Dict[str, Any]:
    try:
        from litellm import completion
    except Exception as exc:
        return {"ok": False, "error": f"litellm import failed: {exc}"}

    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": "请只回复: ok"}],
        "temperature": 0,
        "max_tokens": 10,
        "timeout": timeout,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base

    try:
        resp = completion(**kwargs)
        text = (resp.choices[0].message.content or "").strip()
        return {"ok": True, "response": text}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="覆盖模型名，例如 openai/gpt-4o-mini")
    parser.add_argument("--api-base", default=None, help="覆盖 API Base URL")
    parser.add_argument("--api-key", default=None, help="覆盖 API Key")
    parser.add_argument("--timeout", type=int, default=30, help="超时秒数")
    args = parser.parse_args()

    _bootstrap()
    from app.core.config import settings

    model = _resolve_model(args.model or settings.LLM_MODEL)
    api_base = _normalize_api_base(args.api_base or settings.LLM_BASE_URL)
    api_key = args.api_key if args.api_key is not None else settings.LLM_API_KEY

    _print_section("Config")
    print(f"model={model}")
    print(f"api_base={api_base}")
    print(f"api_key={_mask_key(api_key)}")
    print(f"timeout={args.timeout}s")

    _print_section("Connectivity")
    result = run_test(model=model, api_key=api_key, api_base=api_base, timeout=args.timeout)
    if result["ok"]:
        print(result)
        print("status=OK")
        print(f"response={result['response']!r}")
        return 0

    print("status=FAIL")
    print(f"error={result['error']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
