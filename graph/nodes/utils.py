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
