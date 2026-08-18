from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any

import pandas as pd


CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "delhi ncr": "Delhi NCR",
    "noida": "Noida",
    "pune": "Pune",
}


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "null"}


def clean_string(value: Any) -> str | None:
    if is_blank(value):
        return None
    return re.sub(r"\s+", " ", str(value).strip())


def normalize_name(value: Any) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    text = text.replace(".", " ")
    return re.sub(r"\s+", " ", text.lower()).strip()


def display_name(value: Any) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    if text.isupper():
        return text.title()
    return text


def normalize_email(value: Any) -> str | None:
    text = clean_string(value)
    if not text:
        return None
    text = text.lower()
    return text if "@" in text and "." in text.rsplit("@", 1)[-1] else None


def normalize_phone(value: Any, default_country_code: str = "91") -> str | None:
    if is_blank(value):
        return None
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return None
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 12 and digits.startswith(default_country_code):
        digits = digits[len(default_country_code) :]
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"
    if len(digits) > 10:
        return f"+{digits}"
    return None


def normalize_city(value: Any) -> tuple[str | None, str | None]:
    raw = clean_string(value)
    if not raw:
        return None, None
    key = raw.lower().strip()
    return raw, CITY_ALIASES.get(key, raw.title())


def parse_date(value: Any) -> date | None:
    if is_blank(value):
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def parse_int(value: Any) -> int | None:
    if is_blank(value):
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def parse_ctc(value: Any) -> int | None:
    amount = parse_float(value)
    if amount is None:
        return None
    if 0 < amount < 1000:
        return int(round(amount * 100000))
    return int(round(amount))


def parse_float(value: Any) -> float | None:
    if is_blank(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def parse_bool(value: Any) -> bool | None:
    if is_blank(value):
        return None
    text = str(value).strip().lower()
    if text in {"y", "yes", "true", "1", "verified"}:
        return True
    if text in {"n", "no", "false", "0", "unverified"}:
        return False
    return None


def parse_rate(value: Any) -> tuple[int | None, str | None]:
    text = clean_string(value)
    if not text:
        return None, None
    match = re.fullmatch(r"(?i)(\d+(?:\.\d+)?)(k)?\s*/\s*(hr|hour|month)", text)
    if not match:
        return None, None
    amount = float(match.group(1))
    if match.group(2):
        amount *= 1000
    period = "hour" if match.group(3).lower() in {"hr", "hour"} else "month"
    return int(round(amount)), period


def split_skills(value: Any) -> list[str]:
    text = clean_string(value)
    if not text:
        return []
    skills = []
    for part in text.split(","):
        item = re.sub(r"\s+", " ", part.strip().lower())
        if item and item not in skills:
            skills.append(item)
    return skills


def jsonable(value: Any) -> Any:
    if is_blank(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
