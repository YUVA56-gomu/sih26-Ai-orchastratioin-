import math
import re
import requests
from bs4 import BeautifulSoup
from config import PFZ_URL


def haversine_km(a_lat, a_lon, b_lat, b_lon):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat-a_lat), math.radians(b_lon-a_lon)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371 * 2 * math.asin(math.sqrt(x))


def fetch_advisory_sectors():
    r = requests.get(PFZ_URL, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    # Keep parsing intentionally conservative. The official page's main value is the advisory validity/sector list.
    sectors = []
    for line in soup.stripped_strings:
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) > 2 and line not in sectors:
            sectors.append(line)
    return {"url": r.url, "text": text, "lines": sectors[:300]}


def nearest_advisory(lat, lon):
    try:
        page = fetch_advisory_sectors()
    except Exception as exc:
        return [], {"error": str(exc), "source_url": PFZ_URL}

    # We do not fabricate PFZ coordinates from prose.
    # Return an auditable advisory object and let a real PFZ GIS adapter supply coordinates later.
    return [], {
        "status": "advisory_available_coordinates_require_gis_layer",
        "source_url": page["url"],
        "sample_lines": page["lines"][:80],
    }
