"""
tools/route_service.py
───────────────────────
SAMUDRA AI — Deterministic Marine Route Intelligence Engine

Provides deterministic spatial pathfinding (A* graph search) over a documented
maritime waypoint graph for Indian coastal & offshore waters. Features multi-factor
environmental edge cost evaluation (wind, waves, ocean currents, tides, hazards,
and spatial geofence boundaries) with strict safety and provenance tracking.
"""

from __future__ import annotations

import heapq
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from tools.gis_service import GISService, get_gis_service, haversine_distance_km, distance_to_segment_km


# ── Standalone Spherical Geometry Helpers ─────────────────────────────────────

def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial compass bearing in degrees (0°..360°) from (lat1, lon1) to (lat2, lon2).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    theta = math.atan2(y, x)
    bearing = (math.degrees(theta) + 360.0) % 360.0
    return round(bearing, 1)


# ── Documented Maritime Waypoint Graph ───────────────────────────────────────

# Documented Indian coastal and offshore maritime waypoints for algorithmic route planning.
MARITIME_WAYPOINTS: Dict[str, Dict[str, Any]] = {
    # West Coast (Arabian Sea)
    "wp_kandla":       {"id": "wp_kandla",       "name": "Kandla Port Passage",          "latitude": 22.98, "longitude": 70.22},
    "wp_porbandar":    {"id": "wp_porbandar",    "name": "Porbandar Offshore Node",       "latitude": 21.62, "longitude": 69.58},
    "wp_veraval":      {"id": "wp_veraval",      "name": "Veraval Offshore Node",        "latitude": 20.88, "longitude": 70.35},
    "wp_mumbai":       {"id": "wp_mumbai",       "name": "Mumbai Port Outer Anchorage",  "latitude": 18.92, "longitude": 72.83},
    "wp_murud":        {"id": "wp_murud",        "name": "Murud Coastal Passage",        "latitude": 18.30, "longitude": 72.85},
    "wp_ratnagiri":    {"id": "wp_ratnagiri",    "name": "Ratnagiri Offshore Passage",   "latitude": 16.98, "longitude": 73.25},
    "wp_malvan":       {"id": "wp_malvan",       "name": "Malvan Offshore Node",         "latitude": 16.05, "longitude": 73.45},
    "wp_goa":          {"id": "wp_goa",          "name": "Goa Mormugao Port Outer",      "latitude": 15.49, "longitude": 73.80},
    "wp_karwar":       {"id": "wp_karwar",       "name": "Karwar Coastal Node",          "latitude": 14.80, "longitude": 74.10},
    "wp_mangalore":    {"id": "wp_mangalore",    "name": "New Mangalore Port Outer",     "latitude": 12.92, "longitude": 74.80},
    "wp_kannur":       {"id": "wp_kannur",       "name": "Kannur Offshore Passage",      "latitude": 11.85, "longitude": 75.35},
    "wp_kochi":        {"id": "wp_kochi",        "name": "Kochi Port Outer Anchorage",   "latitude": 9.97,  "longitude": 76.22},
    "wp_kollam":       {"id": "wp_kollam",       "name": "Kollam Offshore Node",         "latitude": 8.88,  "longitude": 76.55},
    "wp_vizhinjam":    {"id": "wp_vizhinjam",    "name": "Vizhinjam Deepwater Port",    "latitude": 8.38,  "longitude": 76.97},
    "wp_kanyakumari":  {"id": "wp_kanyakumari",  "name": "Kanyakumari Maritime Junction", "latitude": 8.05,  "longitude": 77.55},

    # South & East Coast (Gulf of Mannar / Palk Strait / Bay of Bengal)
    "wp_tuticorin":    {"id": "wp_tuticorin",    "name": "Tuticorin Port Outer",         "latitude": 8.75,  "longitude": 78.20},
    "wp_pamban":       {"id": "wp_pamban",       "name": "Pamban Passage Node",          "latitude": 9.28,  "longitude": 79.20},
    "wp_nagapattinam": {"id": "wp_nagapattinam", "name": "Nagapattinam Offshore Node",   "latitude": 10.76, "longitude": 79.86},
    "wp_puducherry":   {"id": "wp_puducherry",   "name": "Puducherry Offshore Node",     "latitude": 11.93, "longitude": 79.85},
    "wp_chennai":      {"id": "wp_chennai",      "name": "Chennai Port Outer Anchorage", "latitude": 13.08, "longitude": 80.30},
    "wp_krishnapatnam":{"id": "wp_krishnapatnam","name": "Krishnapatnam Port Outer",     "latitude": 14.25, "longitude": 80.12},
    "wp_kakinada":     {"id": "wp_kakinada",     "name": "Kakinada Offshore Node",       "latitude": 16.95, "longitude": 82.28},
    "wp_visakhapatnam":{"id": "wp_visakhapatnam","name": "Visakhapatnam Port Outer",    "latitude": 17.68, "longitude": 83.30},
    "wp_paradeep":     {"id": "wp_paradeep",     "name": "Paradeep Port Outer",          "latitude": 20.25, "longitude": 86.68},
    "wp_haldia":       {"id": "wp_haldia",       "name": "Haldia / Hooghly Outer Node",  "latitude": 22.02, "longitude": 88.08},

    # Island & Offshore Nodes
    "wp_kavaratti":    {"id": "wp_kavaratti",    "name": "Kavaratti (Lakshadweep Node)", "latitude": 10.57, "longitude": 72.64},
    "wp_port_blair":   {"id": "wp_port_blair",   "name": "Port Blair (Andaman Node)",    "latitude": 11.67, "longitude": 92.75},
}

# Maritime Highway Network Adjacency Graph (Undirected Edges)
MARITIME_EDGES: List[Tuple[str, str]] = [
    # West Coast Highway
    ("wp_kandla", "wp_porbandar"),
    ("wp_porbandar", "wp_veraval"),
    ("wp_veraval", "wp_mumbai"),
    ("wp_mumbai", "wp_murud"),
    ("wp_murud", "wp_ratnagiri"),
    ("wp_ratnagiri", "wp_malvan"),
    ("wp_malvan", "wp_goa"),
    ("wp_goa", "wp_karwar"),
    ("wp_karwar", "wp_mangalore"),
    ("wp_mangalore", "wp_kannur"),
    ("wp_kannur", "wp_kochi"),
    ("wp_kochi", "wp_kollam"),
    ("wp_kollam", "wp_vizhinjam"),
    ("wp_vizhinjam", "wp_kanyakumari"),

    # Cross-junctions / Offshore connections
    ("wp_mumbai", "wp_ratnagiri"),
    ("wp_ratnagiri", "wp_goa"),
    ("wp_goa", "wp_mangalore"),
    ("wp_mangalore", "wp_kochi"),

    # East Coast Highway
    ("wp_kanyakumari", "wp_tuticorin"),
    ("wp_tuticorin", "wp_pamban"),
    ("wp_pamban", "wp_nagapattinam"),
    ("wp_nagapattinam", "wp_puducherry"),
    ("wp_puducherry", "wp_chennai"),
    ("wp_chennai", "wp_krishnapatnam"),
    ("wp_krishnapatnam", "wp_kakinada"),
    ("wp_kakinada", "wp_visakhapatnam"),
    ("wp_visakhapatnam", "wp_paradeep"),
    ("wp_paradeep", "wp_haldia"),

    # Cross East Coast Connections
    ("wp_kanyakumari", "wp_chennai"),
    ("wp_chennai", "wp_visakhapatnam"),

    # Island Transit Routes
    ("wp_kochi", "wp_kavaratti"),
    ("wp_kanyakumari", "wp_kavaratti"),
    ("wp_chennai", "wp_port_blair"),
    ("wp_visakhapatnam", "wp_port_blair"),
]


# ── Edge Cost Evaluation Engine ─────────────────────────────────────────────

def calculate_segment_cost(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    env_context: Dict[str, Any],
    gis_service: Optional[GISService] = None,
) -> Dict[str, Any]:
    """
    Calculate deterministic multi-factor cost for a route segment (lat1, lon1) -> (lat2, lon2).

    Returns a detailed dictionary with inspectable cost components:
        distance_km, bearing_deg, distance_cost, wind_cost, wave_cost,
        current_cost, tide_cost, hazard_cost, spatial_cost, total_cost.
    """
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    if dist_km <= 1e-6:
        return {
            "distance_km": 0.0,
            "bearing_deg": 0.0,
            "distance_cost": 0.0,
            "wind_cost": 0.0,
            "wave_cost": 0.0,
            "current_cost": 0.0,
            "tide_cost": 0.0,
            "hazard_cost": 0.0,
            "spatial_cost": 0.0,
            "total_cost": 0.0,
            "blocked": False,
        }

    bearing_deg = calculate_bearing_deg(lat1, lon1, lat2, lon2)

    # 1. Wind Cost (Weather Service)
    wind_cost = 0.0
    wx = env_context.get("weather") or env_context.get("weather_data") or {}
    curr_wx = wx.get("current", {}) if isinstance(wx, dict) else {}

    wind_speed = float(curr_wx.get("wind_speed_10m") or 0.0)  # km/h
    wind_dir = float(curr_wx.get("wind_direction_10m") or 0.0) # deg
    wind_gusts = float(curr_wx.get("wind_gusts_10m") or 0.0)  # km/h

    if wind_speed > 0:
        angle_diff = math.radians(abs(bearing_deg - wind_dir))
        # cos_diff: 1.0 when wind blows along bearing (tailwind), -1.0 when blowing against (headwind)
        cos_diff = math.cos(angle_diff)

        if cos_diff < -0.3:  # Headwind
            wind_cost += (wind_speed / 40.0) * 0.25
        elif abs(cos_diff) <= 0.3:  # Crosswind
            wind_cost += (wind_speed / 40.0) * 0.15

        if wind_gusts >= 40.0:
            wind_cost += 0.2

    # 2. Wave Cost (Copernicus / Open-Meteo Marine)
    wave_cost = 0.0
    marine = env_context.get("marine") or env_context.get("marine_data") or env_context.get("ocean_data") or {}
    curr_marine = marine.get("current", {}) if isinstance(marine, dict) else {}

    wave_h = float(curr_marine.get("wave_height") or curr_marine.get("significant_wave_height_m") or 0.0)
    wave_period = float(curr_marine.get("wave_period") or curr_marine.get("mean_wave_period_s") or 0.0)

    if wave_h > 0:
        wave_cost += (wave_h / 2.0) * 0.3
        if wave_h >= 2.0 and wave_period > 0 and wave_period <= 5.0:
            wave_cost += 0.25  # Steep wave penalty

    # 3. Ocean Current Cost (Copernicus / Open-Meteo Marine)
    current_cost = 0.0
    curr_speed = float(curr_marine.get("ocean_current_velocity") or curr_marine.get("speed_ms") or 0.0) # m/s
    curr_dir = float(curr_marine.get("ocean_current_direction") or curr_marine.get("direction_deg") or 0.0) # deg

    if curr_speed > 0:
        angle_diff = math.radians(abs(bearing_deg - curr_dir))
        cos_diff = math.cos(angle_diff)
        # Assisting current reduces cost down to -0.25; opposing current increases cost
        if cos_diff > 0.3:
            current_cost -= min(0.25, (curr_speed / 2.0) * 0.2)
        elif cos_diff < -0.3:
            current_cost += (curr_speed / 2.0) * 0.3

    # 4. Tide Cost (Tide Service)
    tide_cost = 0.0
    tide = env_context.get("tide") or env_context.get("tide_data") or {}
    curr_tide = tide.get("current", {}) if isinstance(tide, dict) else {}
    if curr_tide.get("phase") == "EBBING" and curr_tide.get("sea_level_m", 0) < 0:
        tide_cost += 0.05

    # 5. Hazard Cost (Hazard Service)
    hazard_cost = 0.0
    hazard = env_context.get("hazard") or env_context.get("hazard_data") or {}
    if hazard.get("status") == "ACTIVE" and hazard.get("alerts"):
        hazard_cost += 0.50

    # 6. Spatial Geofence Cost (GIS Service)
    spatial_cost = 0.0
    blocked = False

    if gis_service is None:
        gis_service = get_gis_service()

    # Check midpoint of segment for boundary intersection / proximity
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0
    geo_check = gis_service.check_geofence(mid_lat, mid_lon)

    if geo_check.get("inside_restricted_zone", False):
        spatial_cost = float("inf")
        blocked = True
    elif geo_check.get("proximity_warning", False):
        spatial_cost += 0.15

    # Total cost multiplier
    cost_multiplier = max(0.2, 1.0 + wind_cost + wave_cost + current_cost + tide_cost + hazard_cost + spatial_cost)
    total_cost = dist_km * cost_multiplier if not blocked else float("inf")

    return {
        "distance_km": round(dist_km, 2),
        "bearing_deg": bearing_deg,
        "distance_cost": round(dist_km, 2),
        "wind_cost": round(wind_cost, 4),
        "wave_cost": round(wave_cost, 4),
        "current_cost": round(current_cost, 4),
        "tide_cost": round(tide_cost, 4),
        "hazard_cost": round(hazard_cost, 4),
        "spatial_cost": round(spatial_cost, 4) if not blocked else "BLOCKED",
        "total_cost": round(total_cost, 2) if not blocked else float("inf"),
        "blocked": blocked,
    }


# ── Marine Route Service Class ───────────────────────────────────────────────

class MarineRouteService:
    """Deterministic A* spatial route engine over Indian maritime waters."""

    def __init__(self, gis_service: Optional[GISService] = None):
        self.gis_service = gis_service or get_gis_service()

    def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        origin_name: str = "Origin",
        dest_name: str = "Destination",
        env_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate safe marine route from (origin_lat, origin_lon) to (dest_lat, dest_lon).

        Follows deterministic A* graph search over documented maritime waypoints,
        accounting for weather, waves, ocean currents, tides, hazards, and GIS geofences.
        """
        env_ctx = env_context or {}
        retrieved_at = datetime.now(timezone.utc).isoformat()

        # Validate coordinate bounds
        try:
            origin_lat, origin_lon = float(origin_lat), float(origin_lon)
            dest_lat, dest_lon = float(dest_lat), float(dest_lon)
            if math.isnan(origin_lat) or math.isnan(origin_lon) or math.isnan(dest_lat) or math.isnan(dest_lon):
                raise ValueError("NaN coordinate values provided.")
            if not (-90.0 <= origin_lat <= 90.0 and -180.0 <= origin_lon <= 180.0 and
                    -90.0 <= dest_lat <= 90.0 and -180.0 <= dest_lon <= 180.0):
                raise ValueError(f"Coordinates out of bounds: ({origin_lat}, {origin_lon}) -> ({dest_lat}, {dest_lon})")
        except (TypeError, ValueError) as exc:
            return {
                "status": "UNAVAILABLE",
                "message": f"Invalid coordinate input: {exc}",
                "origin": {"name": origin_name, "latitude": origin_lat, "longitude": origin_lon},
                "destination": {"name": dest_name, "latitude": dest_lat, "longitude": dest_lon},
                "distance_km": 0.0,
                "waypoints": [],
                "segments": [],
                "route_geometry": {"type": "LineString", "coordinates": []},
                "verification": {
                    "eez": "INFORMATIONAL",
                    "mpa": "UNAVAILABLE",
                    "naval": "UNAVAILABLE",
                },
                "provenance": self._get_provenance(retrieved_at),
                "warnings": [f"Invalid input coordinates: {exc}"],
                "retrieved_at": retrieved_at,
            }

        # Check identical origin and destination
        direct_dist = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
        if direct_dist < 0.1:
            origin_node = {"id": "wp_origin", "name": origin_name, "latitude": origin_lat, "longitude": origin_lon}
            dest_node = {"id": "wp_dest", "name": dest_name, "latitude": dest_lat, "longitude": dest_lon}
            return self._build_success_response(
                origin_node, dest_node, [origin_node], [], 0.0, 0.0, env_ctx, retrieved_at
            )


        # Build dynamic graph with origin and destination attached
        graph_nodes, graph_adj = self._build_dynamic_graph(
            origin_lat, origin_lon, origin_name,
            dest_lat, dest_lon, dest_name,
        )

        # Run deterministic A* search
        route_nodes, route_segments, total_dist, total_cost = self._run_astar(
            "wp_origin", "wp_dest", graph_nodes, graph_adj, env_ctx
        )

        if not route_nodes:
            return {
                "status": "UNAVAILABLE",
                "message": (
                    f"No safe marine route could be generated between {origin_name} and {dest_name}. "
                    "Path is either unreachable or blocked by spatial/environmental constraints."
                ),
                "origin": {"name": origin_name, "latitude": origin_lat, "longitude": origin_lon},
                "destination": {"name": dest_name, "latitude": dest_lat, "longitude": dest_lon},
                "distance_km": round(direct_dist, 2),
                "waypoints": [],
                "segments": [],
                "route_geometry": {"type": "LineString", "coordinates": []},
                "verification": {
                    "eez": "INFORMATIONAL",
                    "mpa": "UNAVAILABLE",
                    "naval": "UNAVAILABLE",
                },
                "provenance": self._get_provenance(retrieved_at),
                "retrieved_at": retrieved_at,
            }

        return self._build_success_response(
            graph_nodes["wp_origin"],
            graph_nodes["wp_dest"],
            route_nodes,
            route_segments,
            total_dist,
            total_cost,
            env_ctx,
            retrieved_at,
        )

    def _build_dynamic_graph(
        self,
        o_lat: float, o_lon: float, o_name: str,
        d_lat: float, d_lon: float, d_name: str,
    ) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]]]:
        """Construct dynamic adjacency graph attaching origin & dest to nearest waypoints."""
        nodes: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in MARITIME_WAYPOINTS.items()}
        nodes["wp_origin"] = {"id": "wp_origin", "name": o_name, "latitude": o_lat, "longitude": o_lon}
        nodes["wp_dest"] = {"id": "wp_dest", "name": d_name, "latitude": d_lat, "longitude": d_lon}

        adj: Dict[str, List[str]] = {node_id: [] for node_id in nodes}

        # Add static edges
        for u, v in MARITIME_EDGES:
            if u in nodes and v in nodes:
                adj[u].append(v)
                adj[v].append(u)

        # Attach wp_origin to nearest 4 waypoints
        origin_nearest = sorted(
            [k for k in MARITIME_WAYPOINTS],
            key=lambda k: haversine_distance_km(o_lat, o_lon, nodes[k]["latitude"], nodes[k]["longitude"])
        )[:4]

        for n_id in origin_nearest:
            adj["wp_origin"].append(n_id)
            adj[n_id].append("wp_origin")

        # Attach wp_dest to nearest 4 waypoints
        dest_nearest = sorted(
            [k for k in MARITIME_WAYPOINTS],
            key=lambda k: haversine_distance_km(d_lat, d_lon, nodes[k]["latitude"], nodes[k]["longitude"])
        )[:4]

        for n_id in dest_nearest:
            adj["wp_dest"].append(n_id)
            adj[n_id].append("wp_dest")

        # Direct edge between origin & dest if reasonably close (< 250 km)
        if haversine_distance_km(o_lat, o_lon, d_lat, d_lon) <= 250.0:
            adj["wp_origin"].append("wp_dest")
            adj["wp_dest"].append("wp_origin")

        return nodes, adj

    def _run_astar(
        self,
        start_id: str,
        target_id: str,
        nodes: Dict[str, Dict[str, Any]],
        adj: Dict[str, List[str]],
        env_ctx: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float, float]:
        """Deterministic A* search algorithm."""
        target_node = nodes[target_id]
        target_lat, target_lon = target_node["latitude"], target_node["longitude"]

        # Priority queue stores (f_score, node_id)
        open_set: List[Tuple[float, str]] = []
        heapq.heappush(open_set, (0.0, start_id))

        came_from: Dict[str, str] = {}
        g_score: Dict[str, float] = {node_id: float("inf") for node_id in nodes}
        g_score[start_id] = 0.0

        f_score: Dict[str, float] = {node_id: float("inf") for node_id in nodes}
        f_score[start_id] = haversine_distance_km(
            nodes[start_id]["latitude"], nodes[start_id]["longitude"], target_lat, target_lon
        )

        visited = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == target_id:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()

                # Build nodes & segment metrics
                route_nodes = [nodes[nid] for nid in path]
                segments: List[Dict[str, Any]] = []
                accum_dist = 0.0
                accum_cost = 0.0

                for i in range(len(path) - 1):
                    u_node = nodes[path[i]]
                    v_node = nodes[path[i + 1]]
                    seg_metrics = calculate_segment_cost(
                        u_node["latitude"], u_node["longitude"],
                        v_node["latitude"], v_node["longitude"],
                        env_ctx, self.gis_service
                    )
                    seg_metrics["from_node"] = u_node["id"]
                    seg_metrics["from_name"] = u_node["name"]
                    seg_metrics["to_node"] = v_node["id"]
                    seg_metrics["to_name"] = v_node["name"]
                    segments.append(seg_metrics)

                    accum_dist += seg_metrics["distance_km"]
                    accum_cost += seg_metrics["total_cost"] if isinstance(seg_metrics["total_cost"], (int, float)) else seg_metrics["distance_km"]

                return route_nodes, segments, round(accum_dist, 2), round(accum_cost, 2)

            if current in visited:
                continue
            visited.add(current)

            curr_node = nodes[current]
            curr_lat, curr_lon = curr_node["latitude"], curr_node["longitude"]

            for nbr in adj.get(current, []):
                if nbr in visited:
                    continue

                nbr_node = nodes[nbr]
                seg_cost_data = calculate_segment_cost(
                    curr_lat, curr_lon,
                    nbr_node["latitude"], nbr_node["longitude"],
                    env_ctx, self.gis_service
                )

                if seg_cost_data["blocked"]:
                    continue

                cost = seg_cost_data["total_cost"]
                tentative_g = g_score[current] + cost

                if tentative_g < g_score[nbr]:
                    came_from[nbr] = current
                    g_score[nbr] = tentative_g
                    h = haversine_distance_km(nbr_node["latitude"], nbr_node["longitude"], target_lat, target_lon)
                    f_score[nbr] = tentative_g + h
                    heapq.heappush(open_set, (f_score[nbr], nbr))

        return [], [], 0.0, 0.0

    def _build_success_response(
        self,
        origin_node: Dict[str, Any],
        dest_node: Dict[str, Any],
        route_nodes: List[Dict[str, Any]],
        segments: List[Dict[str, Any]],
        total_dist: float,
        total_cost: float,
        env_ctx: Dict[str, Any],
        retrieved_at: str,
    ) -> Dict[str, Any]:
        """Construct structured success response for calculated route."""
        # LineString coordinates in GeoJSON format: [[lon, lat], [lon, lat], ...]
        geojson_coords = [[n["longitude"], n["latitude"]] for n in route_nodes]

        # Summarize environmental exposure
        wx = env_ctx.get("weather") or env_ctx.get("weather_data") or {}
        curr_wx = wx.get("current", {}) if isinstance(wx, dict) else {}
        marine = env_ctx.get("marine") or env_ctx.get("marine_data") or env_ctx.get("ocean_data") or {}
        curr_marine = marine.get("current", {}) if isinstance(marine, dict) else {}

        env_summary = {
            "wind_speed_kmh": curr_wx.get("wind_speed_10m"),
            "wind_direction_deg": curr_wx.get("wind_direction_10m"),
            "wind_gusts_kmh": curr_wx.get("wind_gusts_10m"),
            "wave_height_m": curr_marine.get("wave_height") or curr_marine.get("significant_wave_height_m"),
            "wave_period_s": curr_marine.get("wave_period") or curr_marine.get("mean_wave_period_s"),
            "current_speed_ms": curr_marine.get("ocean_current_velocity") or curr_marine.get("speed_ms"),
            "current_direction_deg": curr_marine.get("ocean_current_direction") or curr_marine.get("direction_deg"),
        }

        # Data completeness tracking
        data_completeness = {
            "weather": "AVAILABLE" if wx.get("status") in ("OK", "FORECAST_AVAILABLE") else "UNAVAILABLE",
            "marine": "AVAILABLE" if marine.get("status") in ("OK", "PARTIAL") else "UNAVAILABLE",
            "tide": "AVAILABLE" if env_ctx.get("tide_data", {}).get("status") == "AVAILABLE" else "MODELLED",
            "hazard": "AVAILABLE" if env_ctx.get("hazard_data", {}).get("status") == "ACTIVE" else "UNAVAILABLE",
            "eez": "AVAILABLE",
            "mpa": "UNAVAILABLE",
            "naval": "UNAVAILABLE",
        }

        # Warnings array
        warnings = [
            "AI-assisted maritime route decision-support using deterministic waypoint routing and available environmental data.",
            "This is a decision-support route planner, NOT an official nautical-chart navigation or legal maritime clearance system.",
            "Marine Protected Area (MPA) verification is UNAVAILABLE; route cannot be verified against local MPAs.",
            "Naval/defence restriction verification is UNAVAILABLE; route cannot be verified against military restricted areas. Check NHO NAVAREA VIII notices.",
            "EEZ membership is geographic context only and does not represent an official legal restriction boundary.",
        ]


        return {
            "status": "OK",
            "origin": {"name": origin_node["name"], "latitude": origin_node["latitude"], "longitude": origin_node["longitude"]},
            "destination": {"name": dest_node["name"], "latitude": dest_node["latitude"], "longitude": dest_node["longitude"]},
            "distance_km": total_dist,
            "estimated_cost": total_cost,
            "waypoints": route_nodes,
            "segments": segments,
            "route_geometry": {
                "type": "LineString",
                "coordinates": geojson_coords,
            },
            "environmental_summary": env_summary,
            "data_completeness": data_completeness,
            "verification": {
                "eez": "INFORMATIONAL",
                "mpa": "UNAVAILABLE",
                "naval": "UNAVAILABLE",
            },
            "provenance": self._get_provenance(retrieved_at),
            "warnings": warnings,
            "retrieved_at": retrieved_at,
        }

    def _get_provenance(self, retrieved_at: str) -> List[Dict[str, Any]]:
        """Return provenance metadata list for route service."""
        return [
            {
                "service": "SAMUDRA Marine Route Intelligence Engine",
                "algorithm": "Deterministic A* Graph Search over Maritime Waypoint Network",
                "data_class": "DECISION_SUPPORT_HEURISTIC",
                "authority_class": "ALGORITHMIC_MODEL",
                "retrieved_at": retrieved_at,
            },
            {
                "layer_id": "eez_india",
                "provider": "Flanders Marine Institute (VLIZ)",
                "dataset": "Maritime Boundaries Geodatabase (World EEZ v12)",
                "data_class": "INFORMATIONAL_GIS",
                "authority_class": "RESEARCH_INSTITUTION",
                "license": "CC-BY 4.0",
            },
        ]


# ── Global Singleton Instance ────────────────────────────────────────────────

_route_service_instance: Optional[MarineRouteService] = None


def get_route_service() -> MarineRouteService:
    """Return singleton instance of MarineRouteService."""
    global _route_service_instance
    if _route_service_instance is None:
        _route_service_instance = MarineRouteService()
    return _route_service_instance
