"""
graph/nodes/data_weather.py
────────────────────────────
Data Node — Weather (Open-Meteo)

Fetches current conditions and forecast from Open-Meteo.
Skipped if "weather" is not in plan.domains_needed.
"""

from __future__ import annotations

from state.schema import SamudraState
from tools.weather_service import get_weather_conditions
from tools.evidence_service import (
    create_evidence_record,
    AuthorityClass,
    DataClass,
    EvidenceStatus,
    SourceType,
)


def weather_data_node(state: SamudraState) -> SamudraState:
    """Collect weather observations and forecast from Open-Meteo."""

    plan = state.get("plan", {})
    domains = plan.get("domains_needed", [])

    # If this is a recheck pass, only re-fetch if weather was flagged
    recheck_domains = state.get("recheck_domains", [])
    if recheck_domains and "weather" not in recheck_domains:
        return {"node_trace": ["weather_data_collector(recheck_skipped)"]}

    if "weather" not in domains:
        ev = create_evidence_record(
            source_id="weather_open_meteo",
            provider="Open-Meteo",
            dataset="Global Weather Forecast API",
            source_type=SourceType.API,
            authority_class=AuthorityClass.FORECAST,
            data_class=DataClass.FORECAST,
            status=EvidenceStatus.SKIPPED,
            limitations=["Not requested for current query plan"],
        )
        return {
            "weather_data": {"status": "SKIPPED", "reason": "Not required for this query."},
            "evidence": [ev],
            "node_trace": ["weather_data_collector"],
        }

    location = state.get("location", {})

    if location.get("status") != "FOUND":
        ev = create_evidence_record(
            source_id="weather_open_meteo",
            provider="Open-Meteo",
            dataset="Global Weather Forecast API",
            source_type=SourceType.API,
            authority_class=AuthorityClass.FORECAST,
            data_class=DataClass.FORECAST,
            status=EvidenceStatus.UNAVAILABLE,
            limitations=["Location unresolved or invalid"],
        )
        return {
            "weather_data": {
                "status": "BLOCKED",
                "reason": f"Location unavailable: {location.get('status')}",
            },
            "evidence": [ev],
            "node_trace": ["weather_data_collector"],
        }

    try:
        lat = float(location["latitude"])
        lon = float(location["longitude"])
        forecast_days = int(plan.get("forecast_days", 1))
        result = get_weather_conditions(lat, lon, forecast_days)

        is_ok = result.get("status") == "OK"
        ev = create_evidence_record(
            source_id="weather_open_meteo",
            provider="Open-Meteo",
            dataset="Global Weather Forecast API",
            source_type=SourceType.API,
            authority_class=AuthorityClass.FORECAST,
            data_class=DataClass.FORECAST,
            status=EvidenceStatus.AVAILABLE if is_ok else EvidenceStatus.ERROR,
            retrieved_at=(result.get("provenance") or {}).get("retrieved_at"),
            forecast_time=(result.get("current") or {}).get("time"),
            attribution="Open-Meteo (CC BY 4.0)",
            license_type="CC BY 4.0",
            limitations=["Modelled forecast data, not real-time physical weather station reading"],
            query_metadata={"latitude": lat, "longitude": lon, "forecast_days": forecast_days},
        )

        return {
            "weather_data": result,
            "evidence": [ev],
            "node_trace": ["weather_data_collector"],
        }

    except Exception as exc:
        ev = create_evidence_record(
            source_id="weather_open_meteo",
            provider="Open-Meteo",
            dataset="Global Weather Forecast API",
            source_type=SourceType.API,
            authority_class=AuthorityClass.FORECAST,
            data_class=DataClass.FORECAST,
            status=EvidenceStatus.ERROR,
            limitations=[f"Collector exception: {exc}"],
        )
        return {
            "weather_data": {"status": "ERROR", "error": str(exc)},
            "evidence": [ev],
            "errors": [f"weather_data_node: {exc}"],
            "node_trace": ["weather_data_collector"],
        }
