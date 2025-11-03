from __future__ import annotations
"""
Guardrails: JSON validation and simple PII redaction utilities.
"""
from typing import Any, Dict
import re


class Guardrails:
    def __init__(self):
        pass

    def redact_pii(self, text: str) -> str:
        # naive email/phone redaction
        text = re.sub(r"[\w\.-]+@[\w\.-]+", "[REDACTED_EMAIL]", text)
        text = re.sub(r"\b\+?\d[\d\s-]{7,}\b", "[REDACTED_PHONE]", text)
        return text

    def validate_json(self, data: Any, schema: Dict[str, Any]) -> Any:
        # minimal validation (presence of required keys)
        required = (schema or {}).get("required", [])
        if isinstance(data, dict):
            for key in required:
                if key not in data:
                    raise ValueError(f"Missing required key: {key}")
        return data


