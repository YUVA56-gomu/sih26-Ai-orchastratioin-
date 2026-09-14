import os

from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault(
    "OLLAMA_API_BASE",
    os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    ),
)
from agents.marine_orchestrator import marine_orchestrator

root_agent = marine_orchestrator