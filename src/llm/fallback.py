import re

CATEGORY_KEYWORDS = {
    "Technical": ["crash", "bug", "error", "not working", "login", "password", "broken",
                  "freeze", "freezes", "timeout", "500", "sync", "app", "server", "loading"],
    "Billing": ["charge", "invoice", "refund", "payment", "subscription", "billed",
                "credit card", "overcharged", "price", "receipt"],
    "Logistics": ["delivery", "shipping", "package", "order", "tracking", "shipment",
                  "courier", "warehouse", "delivered", "return"],
    "Feedback": ["suggestion", "love", "great", "appreciate", "feature request",
                 "would love", "thank you", "amazing", "improve"],
}

HIGH_PRIORITY_KEYWORDS = [
    "urgent", "asap", "immediately", "critical", "emergency", "down",
    "broken", "not working", "crash", "crashed", "unauthorized",
    "lost all", "cannot access", "can't access", "outage", "data loss",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "issue", "problem", "error", "delay", "delayed", "missing",
    "incorrect", "wrong", "failed", "twice", "overcharged",
]

LOW_PRIORITY_KEYWORDS = [
    "question", "how to", "suggestion", "would love", "great",
    "thank you", "appreciate", "wondering", "feature request",
]

FALLBACK_RESPONSES = {
    "Technical": "Thanks for reporting this technical issue. Our engineering team has been notified and is looking into it.",
    "Billing": "We understand billing concerns can be stressful. Our billing team is reviewing your account now.",
    "Logistics": "We're sorry for the shipping trouble. Our logistics team is checking with the carrier and will update you shortly.",
    "Feedback": "Thank you for sharing your feedback! We've passed this along to our product team.",
}


def classify_offline(text: str) -> dict:
    lowered = text.lower()

    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                scores[cat] += 1

    category = max(scores, key=scores.get)
    if scores[category] == 0:
        category = "Feedback"

    total = sum(scores.values()) or 1
    confidence = round((scores[category] / total) * 100, 1) if scores[category] else 40.0

    high_hits = sum(1 for kw in HIGH_PRIORITY_KEYWORDS if kw in lowered)
    medium_hits = sum(1 for kw in MEDIUM_PRIORITY_KEYWORDS if kw in lowered)
    low_hits = sum(1 for kw in LOW_PRIORITY_KEYWORDS if kw in lowered)
    exclamations = len(re.findall(r"!", text))

    score = (high_hits * 3) + (medium_hits * 1) + (exclamations * 0.5) - (low_hits * 2)
    if score >= 3:
        priority = "High"
    elif score >= 1:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "summary": text[:140],
        "suggested_response": FALLBACK_RESPONSES.get(category, "Thank you for reaching out, our team will follow up shortly."),
        "source": "offline-fallback",
    }
