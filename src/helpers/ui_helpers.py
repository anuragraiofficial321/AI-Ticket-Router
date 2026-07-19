from db import store


PRIORITY_COLORS = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}


def priority_label(priority: str) -> str:
    return f"{PRIORITY_COLORS.get(priority, '⚪')} {priority}"


def source_label(source: str) -> str:
    return "🤖 LLM" if source == "llm" else "📏 Offline"


def add_to_history(user_id: int, text: str, result: dict) -> None:
    """Persist an analyzed ticket against the signed-in user's history."""
    store.add_ticket(user_id, text, result)
