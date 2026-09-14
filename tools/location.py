from __future__ import annotations

import httpx


GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)


def resolve_location(
    place: str,
) -> dict:
    """
    Resolve a human-readable place name into coordinates.
    """

    place = place.strip()

    if not place:
        return {
            "status": "ERROR",
            "message": "Location name is empty.",
        }

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

        data = response.json()

        results = data.get("results") or []

        if not results:

            return {
                "status": "NOT_FOUND",
                "place": place,
            }

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