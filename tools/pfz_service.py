"""
tools/pfz_service.py
────────────────────
Potential Fishing Zone (PFZ) & Fishery Intelligence Orchestration Layer.

Orchestrates:
  1. Copernicus SST grid retrieval & Thermal Front detection (numpy.gradient)
  2. Copernicus Chlorophyll-a grid retrieval & Ocean Productivity analysis
  3. Multi-Factor candidate scoring (SST suitability, front strength, chlorophyll, distance)
  4. Standardized INCOIS / MOSDAC bulletin alignment & status tracking
  5. Multi-source data provenance tracking (MODEL_ANALYSIS, DERIVED, OFFICIAL_BULLETIN)
"""

from __future__ import annotations

from typing import Any, Optional
import math
import numpy as np

from tools.copernicus_grid import get_sst_grid, get_chlorophyll_grid
from tools.pfz_fronts import detect_thermal_fronts, analyze_chlorophyll_productivity
from tools.pfz_scoring import calculate_candidate_score
from tools.incois_bulletin import parse_incois_bulletin, get_default_incois_status


def calculate_pfz_candidates(
    latitude: float,
    longitude: float,
    window_degrees: float = 0.5,
    incois_bulletin: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Calculate evidence-grounded PFZ candidate zones using Copernicus SST thermal fronts,
    Chlorophyll-a ocean productivity boundaries, and multi-factor deterministic scoring.
    """
    lat = float(latitude)
    lon = float(longitude)

    min_lat = lat - window_degrees
    max_lat = lat + window_degrees
    min_lon = lon - window_degrees
    max_lon = lon + window_degrees

    # 1. Retrieve SST grid & Chlorophyll grid with error tolerance
    sst_grid = {}
    chl_grid = {}
    warnings = []

    try:
        sst_grid = get_sst_grid(
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
        )
    except Exception as exc:
        warnings.append(f"SST grid retrieval warning: {exc}")

    try:
        chl_grid = get_chlorophyll_grid(
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
        )
    except Exception as exc:
        warnings.append(f"Chlorophyll grid retrieval warning: {exc}")

    # 2. Front & Productivity Analysis
    thermal_fronts = detect_thermal_fronts(sst_grid) if sst_grid else []
    chl_features = analyze_chlorophyll_productivity(chl_grid) if chl_grid else []

    # 3. Parse INCOIS Bulletin
    bulletin_info = parse_incois_bulletin(incois_bulletin)

    # 4. Generate candidate geographic points for evaluation
    evaluated_points: list[tuple[float, float]] = []

    # Include detected thermal front coordinates
    for front in thermal_fronts[:6]:
        evaluated_points.append((front["latitude"], front["longitude"]))

    # Include detected chlorophyll productivity feature coordinates
    for feat in chl_features[:4]:
        evaluated_points.append((feat["latitude"], feat["longitude"]))

    # Fallback offset grid sampling if no fronts detected
    if not evaluated_points:
        offsets = [
            (0.20, 0.20), (0.20, -0.20), (-0.20, 0.20), (-0.20, -0.20),
            (0.35, 0.00), (-0.35, 0.00), (0.00, 0.35), (0.00, -0.35),
        ]
        for dlat, dlon in offsets:
            evaluated_points.append((lat + dlat, lon + dlon))

    # De-duplicate candidate coordinates
    unique_points: list[tuple[float, float]] = []
    seen = set()
    for pt_lat, pt_lon in evaluated_points:
        key = (round(pt_lat, 3), round(pt_lon, 3))
        if key not in seen:
            seen.add(key)
            unique_points.append((pt_lat, pt_lon))

    # 5. Multi-factor candidate scoring
    candidate_scores = []
    for pt_lat, pt_lon in unique_points:
        # Interpolate or find nearest SST / Chlorophyll values
        sst_val = _extract_nearest_grid_val(sst_grid, pt_lat, pt_lon)
        sst_grad = _extract_nearest_front_grad(thermal_fronts, pt_lat, pt_lon)
        chl_val = _extract_nearest_grid_val(chl_grid, pt_lat, pt_lon)
        chl_grad = _extract_nearest_chl_grad(chl_features, pt_lat, pt_lon)

        scored = calculate_candidate_score(
            candidate_lat=pt_lat,
            candidate_lon=pt_lon,
            target_lat=lat,
            target_lon=lon,
            sst_val=sst_val,
            sst_grad=sst_grad,
            chl_val=chl_val,
            chl_grad=chl_grad,
            incois_bulletin=bulletin_info,
        )
        candidate_scores.append(scored)

    # Sort candidate zones descending by multi-factor score
    candidate_scores.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = candidate_scores[:5]

    # 6. Provenance & Classification
    provenance = []
    if sst_grid:
        provenance.append({
            "parameter": "sea_surface_temperature",
            "dataset_id": sst_grid.get("dataset_id", "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m"),
            "resolution": "0.083deg",
            "data_class": sst_grid.get("status", "OBSERVED"),
            "observation_time": sst_grid.get("observation_time"),
        })

    if chl_grid:
        provenance.append({
            "parameter": "chlorophyll_a",
            "dataset_id": chl_grid.get("dataset_id", "cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m"),
            "resolution": "0.25deg",
            "data_class": chl_grid.get("status", "MODEL_ANALYSIS"),
            "observation_time": chl_grid.get("observation_time"),
        })

    provenance.extend([
        {
            "parameter": "thermal_fronts",
            "method": "numpy.gradient",
            "threshold_c_per_km": 0.05,
            "data_class": "DERIVED",
        },
        {
            "parameter": "pfz_candidates",
            "method": "multi_factor_pfz_score",
            "data_class": "DERIVED",
        },
        bulletin_info.get("provenance", {
            "provider": "INCOIS",
            "data_class": "OFFICIAL_BULLETIN",
            "status": bulletin_info.get("status", "UNAVAILABLE"),
        })
    ])

    status = "CALCULATED" if (sst_grid or chl_grid) else "HEURISTIC"

    return {
        "status": status,
        "source": "Copernicus Marine & Spatial Front Analysis",
        "location": {"latitude": lat, "longitude": lon},
        "nearest_candidate": top_candidates[0] if top_candidates else None,
        "candidates": top_candidates,
        "thermal_fronts": thermal_fronts[:5],
        "chlorophyll_features": chl_features[:5],
        "bulletin": bulletin_info,
        "provenance": provenance,
        "warnings": warnings,
        "important": (
            "This is a decision-support PFZ candidate estimate calculated from spatial "
            "SST thermal fronts and Chlorophyll-a productivity gradients. "
            "Use approved INCOIS/MOSDAC PFZ bulletins for operational fishing zone confirmation."
        ),
    }


def find_nearest_pfz(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """
    Backward compatibility wrapper function for find_nearest_pfz.
    Calls calculate_pfz_candidates and formats output expected by legacy consumers.
    """
    res = calculate_pfz_candidates(latitude, longitude)
    # Ensure legacy keys exist
    if "pfz_candidates" not in res:
        res["pfz_candidates"] = res.get("candidates", [])
    if "pfz_status" not in res:
        res["pfz_status"] = res.get("status", "HEURISTIC")
    return res


# ── Grid Lookup Helper Functions ──────────────────────────────────────────────
def _extract_nearest_grid_val(grid_dict: dict[str, Any], lat: float, lon: float) -> Optional[float]:
    if not isinstance(grid_dict, dict) or "values" not in grid_dict:
        return None
    lats = grid_dict.get("latitudes", [])
    lons = grid_dict.get("longitudes", [])
    raw_vals = grid_dict.get("values", [])
    if not lats or not lons or not raw_vals:
        return None

    val_arr = np.asarray(raw_vals, dtype=np.float64)
    if val_arr.ndim == 1 and len(lats) * len(lons) == val_arr.size:
        val_arr = val_arr.reshape((len(lats), len(lons)))
    elif val_arr.ndim != 2:
        return None

    r_idx = int(np.argmin(np.abs(np.asarray(lats) - lat)))
    c_idx = int(np.argmin(np.abs(np.asarray(lons) - lon)))

    v = float(val_arr[r_idx, c_idx])
    return None if np.isnan(v) else v


def _extract_nearest_front_grad(fronts: list[dict[str, Any]], lat: float, lon: float) -> Optional[float]:
    if not fronts:
        return None
    best_grad = None
    min_dist = 999.0
    for f in fronts:
        flat = f.get("latitude", 0.0)
        flon = f.get("longitude", 0.0)
        dist = math.hypot((lat - flat) * 111.0, (lon - flon) * 106.0)
        if dist < min_dist:
            min_dist = dist
            best_grad = f.get("gradient_c_per_km")
    return best_grad if min_dist <= 25.0 else 0.0


def _extract_nearest_chl_grad(features: list[dict[str, Any]], lat: float, lon: float) -> Optional[float]:
    if not features:
        return None
    best_grad = None
    min_dist = 999.0
    for f in features:
        flat = f.get("latitude", 0.0)
        flon = f.get("longitude", 0.0)
        dist = math.hypot((lat - flat) * 111.0, (lon - flon) * 106.0)
        if dist < min_dist:
            min_dist = dist
            best_grad = f.get("chlorophyll_gradient")
    return best_grad if min_dist <= 35.0 else 0.0