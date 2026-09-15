"""
main.py
────────
SAMUDRA.AI entry point.

Run with:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
from dotenv import load_dotenv

load_dotenv()

from api.samudra_api import app  # noqa: E402  (load_dotenv must come first)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
