import requests
from bs4 import BeautifulSoup

DISTRICT_WARNINGS = "https://mausam.imd.gov.in/api/warnings_district_api.php"
DISTRICT_NOWCAST = "https://mausam.imd.gov.in/api/nowcast_district_api.php"
CYCLONE_PAGE = "https://mausam.imd.gov.in/responsive/cycloneinformation.php?lang=en"


def _get_json(url, params=None):
    r = requests.get(url, params=params, timeout=20, headers={"User-Agent": "ORCA-Marine-Intelligence/1.0"})
    r.raise_for_status()
    return r.json()


def district_warnings(location_name: str):
    try:
        data = _get_json(DISTRICT_WARNINGS)
    except Exception as exc:
        return [], {"status": "unavailable", "error": str(exc), "source_url": DISTRICT_WARNINGS}
    items = data if isinstance(data, list) else data.get("data", data.get("districts", [])) if isinstance(data, dict) else []
    text = str(items)
    if location_name.lower() not in text.lower():
        # Keep a transparent result rather than pretending a district match.
        return [], {"status": "no_location_match", "source_url": DISTRICT_WARNINGS}
    matches = []
    for item in items if isinstance(items, list) else []:
        s = str(item)
        if location_name.lower() in s.lower():
            matches.append(item)
    return matches[:10], {"status": "ok", "source_url": DISTRICT_WARNINGS}


def district_nowcast(location_name: str):
    try:
        data = _get_json(DISTRICT_NOWCAST)
    except Exception as exc:
        return [], {"status": "unavailable", "error": str(exc), "source_url": DISTRICT_NOWCAST}
    items = data if isinstance(data, list) else data.get("data", data.get("districts", [])) if isinstance(data, dict) else []
    text = str(items)
    if location_name.lower() not in text.lower():
        return [], {"status": "no_location_match", "source_url": DISTRICT_NOWCAST}
    matches = [x for x in items if location_name.lower() in str(x).lower()] if isinstance(items, list) else []
    return matches[:10], {"status": "ok", "source_url": DISTRICT_NOWCAST}


def cyclone_status():
    try:
        r = requests.get(CYCLONE_PAGE, timeout=20, headers={"User-Agent": "ORCA-Marine-Intelligence/1.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        return {"status": "page_available", "summary": text[:4000], "source_url": r.url}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc), "source_url": CYCLONE_PAGE}
