"""
api/models.py
──────────────
Pydantic request / response models for the SAMUDRA.AI API.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's natural language query")
    thread_id: str = Field(
        default="default",
        description="Conversation thread ID for multi-turn memory",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Optional explicit latitude (overrides location in query)",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Optional explicit longitude (overrides location in query)",
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Final synthesized response")
    detected_language: str = Field(default="en")
    intent: str = Field(default="general")
    risk_level: str = Field(default="UNKNOWN")
    risk_score: int = Field(default=-1)
    confidence_score: float = Field(default=1.0)
    gate_decision: str = Field(default="PASS")
    node_trace: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    location: Optional[dict[str, Any]] = None
    thread_id: str = Field(default="default")


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "SAMUDRA.AI"
    version: str = "1.0.0-langgraph"
