from dataclasses import dataclass

@dataclass
class Plan:
    tasks: list[str]


def build_plan(intent):
    tasks = ["resolve_location", "fetch_marine", "fetch_weather"]
    p = set(intent.requested_parameters)
    if intent.requires_pfz or intent.intent in {"pfz", "fishing_zone", "nearest_pfz"}:
        tasks.append("fetch_pfz")
    if intent.hazards or intent.intent in {"safety", "alerts", "safe_venture"}:
        tasks.append("fetch_imd_alerts")
    if any(x in p for x in {"salinity", "chlorophyll", "mixed_layer_depth"}) or intent.requires_productivity:
        tasks.append("fetch_incois_erddap")
    if intent.requires_geofence:
        tasks.append("check_geofence")
    if intent.requires_route:
        tasks.append("route_analysis")
    return Plan(tasks=list(dict.fromkeys(tasks)))
