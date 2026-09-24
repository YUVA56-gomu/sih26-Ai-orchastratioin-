import json
import math
from pathlib import Path
from shapely.geometry import shape, Point
from config import ORCA_GEOFENCE_FILE


def _distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371 * 2 * math.asin(math.sqrt(x))


def check_geofences(lat, lon):
    path = Path(ORCA_GEOFENCE_FILE)
    if not path.exists():
        return [], {"status": "no_geofence_dataset_configured"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    p = Point(lon, lat)
    hits = []
    for feature in payload.get("features", []):
        geom = shape(feature["geometry"])
        props = feature.get("properties", {})
        inside = geom.contains(p) or geom.touches(p)
        # Approximate distance using a local degree-to-km conversion around point.
        distance_km = 0.0 if inside else geom.distance(p) * 111.0
        hits.append({
            "name": props.get("name", "Unnamed zone"),
            "zone_type": props.get("type", "restricted"),
            "inside": inside,
            "distance_km": round(distance_km, 3),
            "source": props.get("source", "Configured GeoJSON"),
        })
    return hits, {"status": "ok", "count": len(hits)}
