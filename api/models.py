"""
api/models.py
──────────────
Pydantic request / response models for the SAMUDRA.AI API.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: Optional[str] = Field(
        default=None,
        description="User's natural language query (primary input field)",
    )
    query: Optional[str] = Field(
        default=None,
        description="Legacy field for user query (backward compatibility)",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Public conversation identifier for multi-turn context",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Internal thread identifier for LangGraph memory",
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
    conversation_id: str = Field(..., description="Public conversation identifier")
    thread_id: str = Field(..., description="Internal LangGraph thread identifier")
    response: str = Field(..., description="Final synthesized response")
    route_path: Optional[str] = Field(default="DEEP", description="Execution path: FAST or DEEP")
    detected_language: str = Field(default="en")
    intent: str = Field(default="general")
    risk_level: Optional[str] = Field(default=None)
    risk_score: Optional[int] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None)
    gate_decision: Optional[str] = Field(default=None)
    node_trace: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    location: Optional[dict[str, Any]] = None
    active_context: Optional[dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "SAMUDRA.AI"
    version: str = "1.0.0-langgraph"
