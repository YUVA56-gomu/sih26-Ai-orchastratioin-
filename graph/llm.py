"""
graph/llm.py
────────────
Single place to build the LLM instance used across all graph nodes.
Controlled by the LLM_PROVIDER env variable:
  gemini  → Google Gemini via langchain-google-genai
  groq    → Groq (Llama 3.3-70B) via langchain-groq
  ollama  → Local Ollama via langchain-ollama
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


def get_llm(temperature: float = 0.1):
    """Return a LangChain chat model based on LLM_PROVIDER."""

    if _PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    if _PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
        )

    # default: gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
