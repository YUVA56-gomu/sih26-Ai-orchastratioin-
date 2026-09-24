from __future__ import annotations

import httpx


GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)


PREDEFINED_COASTAL_LOCATIONS = {
    "karwar": {"name": "Karwar", "latitude": 14.81, "longitude": 74.12, "country": "India", "admin1": "Karnataka"},
    "visakhapatnam": {"name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21, "country": "India", "admin1": "Andhra Pradesh"},
    "vishakapatnam": {"name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21, "country": "India", "admin1": "Andhra Pradesh"},
    "vizag": {"name": "Visakhapatnam", "latitude": 17.68, "longitude": 83.21, "country": "India", "admin1": "Andhra Pradesh"},
    "chennai": {"name": "Chennai", "latitude": 13.08, "longitude": 80.27, "country": "India", "admin1": "Tamil Nadu"},
    "kochi": {"name": "Kochi", "latitude": 9.93, "longitude": 76.26, "country": "India", "admin1": "Kerala"},
    "cochin": {"name": "Kochi", "latitude": 9.93, "longitude": 76.26, "country": "India", "admin1": "Kerala"},
    "mumbai": {"name": "Mumbai", "latitude": 18.94, "longitude": 72.84, "country": "India", "admin1": "Maharashtra"},
    "goa": {"name": "Goa", "latitude": 15.29, "longitude": 73.98, "country": "India", "admin1": "Goa"},
    "mangalore": {"name": "Mangaluru", "latitude": 12.91, "longitude": 74.85, "country": "India", "admin1": "Karnataka"},
    "mangaluru": {"name": "Mangaluru", "latitude": 12.91, "longitude": 74.85, "country": "India", "admin1": "Karnataka"},
    "pondicherry": {"name": "Puducherry", "latitude": 11.94, "longitude": 79.80, "country": "India", "admin1": "Puducherry"},
    "puducherry": {"name": "Puducherry", "latitude": 11.94, "longitude": 79.80, "country": "India", "admin1": "Puducherry"},
    "trivandrum": {"name": "Thiruvananthapuram", "latitude": 8.52, "longitude": 76.93, "country": "India", "admin1": "Kerala"},
    "thiruvananthapuram": {"name": "Thiruvananthapuram", "latitude": 8.52, "longitude": 76.93, "country": "India", "admin1": "Kerala"},
    "paradeep": {"name": "Paradeep", "latitude": 20.31, "longitude": 86.61, "country": "India", "admin1": "Odisha"},
    "tuticorin": {"name": "Thoothukudi", "latitude": 8.76, "longitude": 78.13, "country": "India", "admin1": "Tamil Nadu"},
    "porbandar": {"name": "Porbandar", "latitude": 21.64, "longitude": 69.60, "country": "India", "admin1": "Gujarat"},
    "veraval": {"name": "Veraval", "latitude": 20.90, "longitude": 70.37, "country": "India", "admin1": "Gujarat"},
    "kanyakumari": {"name": "Kanyakumari", "latitude": 8.08, "longitude": 77.53, "country": "India", "admin1": "Tamil Nadu"},
}


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

    lower_place = place.lower()
    if lower_place in PREDEFINED_COASTAL_LOCATIONS:
        info = PREDEFINED_COASTAL_LOCATIONS[lower_place]
        return {
            "status": "FOUND",
            "name": info["name"],
            "country": info["country"],
            "admin1": info["admin1"],
            "latitude": info["latitude"],
            "longitude": info["longitude"],
            "source": "Predefined Coastal Index",
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