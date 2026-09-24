import math
import requests
import xml.etree.ElementTree as ET

ACTIVE_URL = "https://www.ndbc.noaa.gov/activestations.xml"
REALTIME_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"


def haversine_km(a_lat, a_lon, b_lat, b_lon):
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(x))


def nearest_station(lat, lon):
    r = requests.get(ACTIVE_URL, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    best = None
    for node in root.findall(".//station"):
        try:
            slat = float(node.attrib["lat"])
            slon = float(node.attrib["lon"])
        except (KeyError, ValueError):
            continue
        sid = node.attrib.get("id")
        if not sid:
            continue
        d = haversine_km(lat, lon, slat, slon)
        row = (d, sid, slat, slon, node.attrib.get("name", sid))
        if best is None or row[0] < best[0]:
            best = row
    return best


def fetch_nearest_observation(lat, lon, max_distance_km=600):
    best = nearest_station(lat, lon)
    if not best or best[0] > max_distance_km:
        return None
    distance, station, slat, slon, name = best
    url = REALTIME_URL.format(station=station)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    lines = [x for x in r.text.splitlines() if x.strip()]
    header = None
    row = None
    for line in lines:
        if line.startswith("#YY"):
            header = line.lstrip("#").split()
        elif not line.startswith("#"):
            row = line.split()
            break
    if not header or not row:
        return None
    values = {k: row[i] for i, k in enumerate(header) if i < len(row)}

    def num(key):
        value = values.get(key)
        if value in (None, "MM", "NaN", "nan"):
            return None
        try:
            return float(value)
        except ValueError:
            return None

    timestamp = None
    parts = [values.get("YY"), values.get("MM"), values.get("DD"), values.get("hh"), values.get("mm")]
    if all(x and x.isdigit() for x in parts):
        timestamp = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}T{parts[3].zfill(2)}:{parts[4].zfill(2)}:00Z"

    return {
        "station": station,
        "name": name,
        "distance_km": round(distance, 2),
        "latitude": slat,
        "longitude": slon,
        "timestamp": timestamp,
        "source": "NOAA NDBC",
        "source_url": url,
        "data": {
            "wave_height": num("WVHT"),
            "wave_period": num("DPD"),
            "wave_direction": num("MWD"),
            "wind_speed": num("WSPD"),
            "wind_direction": num("WDIR"),
            "pressure": num("PRES"),
            "water_temperature": num("WTMP"),
        },
    }
