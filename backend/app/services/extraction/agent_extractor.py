import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from .models import (
    BudgetInfo,
    ContactInfo,
    DeadlineInfo,
    ExtractedInfo,
    ExtractionResult,
    QualificationInfo,
)


class AgentExtractionService:
    """基于 LiteLLM 的结构化信息抽取服务。"""

    def __init__(self):
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = self._normalize_api_base(settings.LLM_BASE_URL)
        self.timeout_seconds = int(getattr(settings, "LLM_TIMEOUT_SECONDS", 30) or 30)

    def extract(self, content: str, title: str = "") -> ExtractionResult:
        if not content.strip():
            return ExtractionResult(
                success=False,
                info=ExtractedInfo(),
                errors=["内容为空，无法进行 Agent 抽取"],
            )

        try:
            response_text = self._call_llm(content=content, title=title)
            payload = self._parse_json(response_text)
            info = self._payload_to_info(payload)
            return ExtractionResult(success=True, info=info)
        except Exception as exc:
            return ExtractionResult(
                success=False,
                info=ExtractedInfo(),
                errors=[f"Agent 抽取失败: {exc}"],
            )

    def _call_llm(self, content: str, title: str) -> str:
        try:
            from litellm import completion
        except Exception as exc:
            raise RuntimeError(f"litellm 未安装或不可用: {exc}") from exc

        system_prompt = (
            "你是招标公告结构化抽取助手。"
            "请从文本中提取字段并返回纯 JSON，不要 markdown，不要额外解释。"
        )
        user_prompt = f"""
请提取以下字段并返回 JSON（字段缺失时返回 null 或空数组）：
{{
  "budget_wanyuan": number | null,
  "deadline": "YYYY-MM-DD" | "YYYY-MM-DD HH:MM" | null,
  "qualifications": string[],
  "tags": string[],
  "region": string | null,
  "project_type": string | null,
  "contact_person": string | null,
  "contact_phone": string | null,
  "contact_email": string | null,
  "confidence": number
}}

标题：
{title}

正文：
{content[:12000]}
"""
        model_name = self.model if "/" in self.model else f"openai/{self.model}"
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1200,
            "timeout": self.timeout_seconds,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        response = completion(**kwargs)
        content_text = response.choices[0].message.content or ""
        return str(content_text)

    def _normalize_api_base(self, value: str) -> str:
        raw = str(value or "").strip().rstrip("/")
        if not raw:
            return raw
        if raw.endswith("/chat/completions"):
            return raw[: -len("/chat/completions")]
        return raw

    def _parse_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if not match:
                raise ValueError("LLM 返回中未找到 JSON 对象")
            return json.loads(match.group(0))

    def _payload_to_info(self, payload: Dict[str, Any]) -> ExtractedInfo:
        confidence = self._to_float(payload.get("confidence"), default=0.75)
        budget_value = self._to_float(payload.get("budget_wanyuan"), default=None)
        deadline_raw = payload.get("deadline")

        info = ExtractedInfo(
            budget=BudgetInfo(
                value=budget_value,
                unit="万元",
                confidence=confidence,
                source="agent_litellm",
            ),
            deadline=DeadlineInfo(
                value=self._parse_datetime(deadline_raw),
                raw_text=str(deadline_raw or ""),
                confidence=confidence,
            ),
            qualifications=QualificationInfo(
                required=self._to_list(payload.get("qualifications")),
                confidence=confidence,
            ),
            contact=ContactInfo(
                person=str(payload.get("contact_person") or ""),
                phone=str(payload.get("contact_phone") or ""),
                email=str(payload.get("contact_email") or ""),
                confidence=confidence,
            ),
            tags=self._to_list(payload.get("tags")),
            region=str(payload.get("region") or ""),
            project_type=str(payload.get("project_type") or ""),
        )
        return info

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        raw = str(value).strip()
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%Y.%m.%d %H:%M",
            "%Y.%m.%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt)
            except Exception:
                continue
        return None

    def _to_list(self, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        if not text:
            return []
        return [text]

    def _to_float(self, value: Any, default: Optional[float]) -> Optional[float]:
        if value is None:
            return default
        try:
            return float(value)
        except Exception:
            return default
