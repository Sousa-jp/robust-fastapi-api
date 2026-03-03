import re
from typing import Any

_SQL_AND_XSS = "|".join(
    [
        r"(?:union\s+select)",
        r"(?:insert\s+into\s+\w+)",
        r"(?:delete\s+from\s+\w+)",
        r"(?:drop\s+(?:table|database|schema))",
        r"(?:[\'\"].*(?:\bor\b|\band\b).*[\'\"]\s*=\s*[\'\"])",
        r"(?:\;\s*(?:drop|delete|insert|update|truncate|create))",
        r"(?:--\s*$)",
        r"(?:/\*[\s\S]*\*/)",
        r"(?:(?:\s|^)(?:xp_|sp_)\w+)",
        r"(?:benchmark\s*\()",
        r"(?:sleep\s*\()",
        r"(?:waitfor\s+delay)",
        r"(?:<script[\s>])",
        r"(?:javascript\s*:)",
        r"(?:vbscript\s*:)",
        r"(?:on\w+\s*=)",
        r"(?:<iframe[\s>])",
        r"(?:<object[\s>])",
        r"(?:<embed[\s>])",
        r"(?:eval\s*\()",
        r"(?:expression\s*\()",
        r"(?:<img[^>]+onerror\s*=)",
        r"(?:<svg[\s>].*onload\s*=)",
    ]
)

_DANGEROUS = re.compile(f"(?:{_SQL_AND_XSS})", re.I | re.M | re.S)


def is_dangerous(value: str) -> bool:
    if not isinstance(value, str):
        return False
    s = value.strip()
    if not s:
        return False
    return _DANGEROUS.search(s) is not None


def _check_value(obj: Any) -> bool:
    if isinstance(obj, str):
        return is_dangerous(obj)
    if isinstance(obj, dict):
        return any(_check_value(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_check_value(item) for item in obj)
    if isinstance(obj, bytes):
        try:
            return is_dangerous(obj.decode("utf-8", errors="replace"))
        except Exception:
            return True
    return False


def payload_contains_attack(obj: Any) -> bool:
    return _check_value(obj)
