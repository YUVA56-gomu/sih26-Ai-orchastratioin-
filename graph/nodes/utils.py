"""
graph/nodes/utils.py
────────────────────
Utility functions for graph node implementations.
"""

def extract_text(response) -> str:
    """Safely extract string text content from a LangChain LLM response."""
    if response is None:
        return ""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, str):
                texts.append(block)
            elif isinstance(block, dict) and "text" in block:
                texts.append(str(block.get("text", "")))
        return "".join(texts).strip()
    return str(content).strip()


def format_recent_history(state: dict, max_messages: int = 6) -> str:
    """Format recent turns from messages or conversation_history alongside context_summary for LLM prompts."""
    summary = state.get("context_summary")
    msgs = state.get("messages") or state.get("conversation_history") or []

    sections = []
    if summary and isinstance(summary, str) and summary.strip():
        sections.append(f"Long-term Conversation Summary:\n{summary.strip()}")

    if msgs:
        recent = msgs[-max_messages:]
        formatted = []
        for m in recent:
            if isinstance(m, dict):
                role = m.get("role", "user").capitalize()
                content = m.get("content") or m.get("text") or ""
            else:
                role_raw = getattr(m, "type", "user").lower()
                if role_raw in ("human", "user"):
                    role = "User"
                elif role_raw in ("ai", "assistant"):
                    role = "Assistant"
                else:
                    role = role_raw.capitalize()
                content = getattr(m, "content", str(m))
            if content:
                formatted.append(f"{role}: {content}")

        if formatted:
            sections.append("Recent Conversation History:\n" + "\n".join(formatted))

    if not sections:
        return ""

    return "\n\n".join(sections)




def format_active_context(state: dict) -> str:
    """Format active_context (location, timeframe, active topic) for LLM prompts."""
    ctx = state.get("active_context") or {}
    if not ctx:
        return ""

    lines = []
    loc = ctx.get("location")
    if isinstance(loc, dict) and loc.get("status") == "FOUND":
        name = loc.get("name") or f"{loc.get('latitude')}, {loc.get('longitude')}"
        lines.append(f"Active Location Context: {name} (Lat: {loc.get('latitude')}, Lon: {loc.get('longitude')})")

    if ctx.get("time_request"):
        lines.append(f"Active Time Frame: {ctx.get('time_request')}")

    if ctx.get("topic"):
        lines.append(f"Active Domain Topic: {ctx.get('topic')}")

    if not lines:
        return ""

    return "Active Conversation Context:\n" + "\n".join(lines)
