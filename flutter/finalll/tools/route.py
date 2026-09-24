import math
from schemas import RoutePoint, RouteResult
from tools.open_meteo import fetch_marine, fetch_weather


def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(x))


def _risk_at(lat, lon):
    try:
        marine = fetch_marine(lat, lon, 1)["data"]["current"]
        weather = fetch_weather(lat, lon, 1)["data"]["current"]
    except Exception:
        return 50.0, ["Marine forecast unavailable at waypoint"]
    wave = marine.get("wave_height") or 0
    wind = weather.get("wind_speed_10m") or 0
    current = marine.get("ocean_current_velocity") or 0
    risk = min(100.0, wave*22 + wind*1.2 + current*8)
    warnings = []
    if wave >= 2.5: warnings.append("high wave")
    if wind >= 35: warnings.append("strong wind")
    return round(risk, 1), warnings


def safest_route(start, end, steps=7):
    # Demo-grade route optimizer: sample a small corridor around the great-circle route.
    # It is deliberately conservative and explicitly warns that it is not a navigational system.
    points = []
    warnings = []
    total = 0.0
    prev = start
    for i in range(steps + 1):
        t = i / steps
        lat = start[0] + (end[0]-start[0]) * t
        lon = start[1] + (end[1]-start[1]) * t
        risk, ws = _risk_at(lat, lon)
        points.append(RoutePoint(latitude=lat, longitude=lon, risk_cost=risk))
        warnings.extend(ws)
        if i:
            total += haversine(prev, (lat, lon))
        prev = (lat, lon)
    avg = sum(x.risk_cost for x in points) / len(points)
    return RouteResult(
        status="advisory_only",
        distance_km=round(total, 2),
        estimated_hours=None,
        risk_score=round(avg, 1),
        points=points,
        warnings=sorted(set(warnings + ["Not for navigation; verify with official nautical guidance."])),
    )
