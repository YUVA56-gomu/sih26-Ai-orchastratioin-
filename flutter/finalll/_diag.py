"""Reproduce the chat-pipeline 500 and print the full traceback."""
import traceback
from session_store import SessionStore, init_db
from agents.orchestrator import Orchestrator
from schemas import Location

init_db()
orc = Orchestrator(SessionStore())
loc = Location(latitude=9.9312, longitude=76.2673, name="Kochi")

# Step through the pipeline for a non-greeting query to find the throwing stage.
try:
    result = orc.run("sea conditions near Kochi", None, loc)
    print("OK - no exception. request_id:", result.request_id)
    print("answer.summary:", result.answer.get("summary"))
except Exception:
    traceback.print_exc()
