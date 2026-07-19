import json
import re
from config.settings import VALID_CATEGORIES, VALID_PRIORITIES


def extract_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json", "", cleaned.strip())
    cleaned = re.sub(r"^```", "", cleaned.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def normalize_result(parsed: dict, original_text: str, source: str) -> dict:
    category = parsed.get("category", "")
    priority = parsed.get("priority", "")

    if category not in VALID_CATEGORIES:
        category = "Feedback"
    if priority not in VALID_PRIORITIES:
        priority = "Low"

    confidence = parsed.get("confidence", 50)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 50.0
    confidence = max(0.0, min(100.0, confidence))

    return {
        "category": category,
        "priority": priority,
        "confidence": round(confidence, 1),
        "summary": parsed.get("summary", original_text[:140]),
        "suggested_response": parsed.get(
            "suggested_response",
            "Thank you for reaching out, our team will follow up shortly.",
        ),
        "source": source,
    }
