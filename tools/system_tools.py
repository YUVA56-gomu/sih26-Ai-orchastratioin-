from __future__ import annotations

import requests


def check_ollama() -> dict:
    """
    Verify that the local Ollama server is reachable.
    """

    url = "http://localhost:11434/api/tags"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        models = [
            model.get("name")
            for model in data.get("models", [])
        ]

        return {
            "status": "online",
            "models": models,
        }

    except Exception as exc:
        return {
            "status": "offline",
            "error": str(exc),
        }