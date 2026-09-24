import requests
from urllib.parse import quote
from config import INCOIS_ERDDAP_BASE, INCOIS_CHL_DATASET, INCOIS_MLD_DATASET


def _query(dataset, variable, lat, lon):
    query = f"{variable}[(last)][({lat})][({lon})]"
    encoded = quote(query, safe="[]():+-")
    url = f"{INCOIS_ERDDAP_BASE}/griddap/{dataset}.json?{encoded}"
    r = requests.get(url, timeout=35)
    r.raise_for_status()
    return url, r.json()


def _extract(response):
    table = response.get("table", {})
    rows = table.get("rows", [])
    cols = table.get("columnNames", [])
    units = table.get("columnUnits", [])
    if not rows:
        return None
    row = rows[0]
    obj = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
    unit_map = {cols[i]: units[i] for i in range(min(len(cols), len(units)))}
    for key, value in obj.items():
        if key in {"time", "latitude", "longitude"}:
            continue
        if isinstance(value, (int, float)):
            return {"value": float(value), "unit": unit_map.get(key), "timestamp": obj.get("time")}
    return None


def fetch_satellite_points(lat, lon):
    out = {}
    try:
        url, raw = _query(INCOIS_CHL_DATASET, "CHLOROPHYLL", lat, lon)
        x = _extract(raw)
        if x: out["chlorophyll"] = {**x, "url": url}
    except Exception as exc:
        out["chlorophyll_error"] = str(exc)
    try:
        url, raw = _query(INCOIS_MLD_DATASET, "MLD", lat, lon)
        x = _extract(raw)
        if x: out["mixed_layer_depth"] = {**x, "url": url}
    except Exception as exc:
        out["mld_error"] = str(exc)
    return out
