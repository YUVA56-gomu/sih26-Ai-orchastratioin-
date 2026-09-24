import requests

URL = "https://nominatim.openstreetmap.org/search"


def resolve_location(name: str) -> dict:
    r = requests.get(
        URL,
        params={"q": name, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": "ORCA-Marine-Intelligence/1.0"},
        timeout=15,
    )
    r.raise_for_status()
    items = r.json()
    if not items:
        raise ValueError(f"Could not geocode location: {name}")
    item = items[0]
    return {
        "name": item.get("display_name", name).split(",")[0],
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
        "source": "OpenStreetMap Nominatim",
        "source_url": r.url,
    }
