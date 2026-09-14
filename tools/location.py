from __future__ import annotations

import re
import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

_COORD_RE = re.compile(
    r"(?P<lat>-?\d+(?:\.\d+)?)\s*[, ]\s*(?P<lon>-?\d+(?:\.\d+)?)"
)


def resolve_location_query(query: str) -> dict:
    """Resolve coordinates from text, or geocode a place name found in the query."""
    query = (query or "").strip()

    match = _COORD_RE.search(query)
    if match:
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return {
                "status": "FOUND",
                "name": "Explicit coordinates",
                "latitude": lat,
                "longitude": lon,
                "source": "User-provided coordinates",
            }

    # Pull the most likely place phrase from common planner output.
    cleaned = query
    for marker in ["location:", "place:", "from", "near"]:
        cleaned = cleaned.replace(marker, " ")

    candidates = [
        "Visakhapatnam",
        "Goa",
        "Karwar",
        "Mumbai",
        "Chennai",
        "Kochi",
        "Mangalore",
        "Andhra Pradesh",
    ]

    place = next(
        (name for name in candidates if name.lower() in query.lower()),
        None,
    )

    if place is None:
        # Last-resort geocoding with the planner's concise text.
        place = cleaned[:120]

    if not place:
        return {"status": "NOT_FOUND", "error": "No location supplied."}

    try:
        response = httpx.get(
            GEOCODING_URL,
            params={
                "name": place,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            return {"status": "NOT_FOUND", "place": place}

        item = results[0]
        return {
            "status": "FOUND",
            "name": item.get("name"),
            "country": item.get("country"),
            "admin1": item.get("admin1"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "timezone": item.get("timezone"),
            "source": "Open-Meteo Geocoding",
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "place": place,
            "error": str(exc),
        }
