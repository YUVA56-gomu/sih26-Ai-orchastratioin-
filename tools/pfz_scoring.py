"""
tools/pfz_scoring.py
────────────────────
Multi-Factor Deterministic PFZ Candidate Scoring Engine.

Combines:
  1. SST Suitability (optimal 26°C – 29°C range heuristic)
  2. SST Thermal Front Strength (∇SST gradient)
  3. Chlorophyll Concentration
  4. Chlorophyll Gradient (∇CHL productivity boundary)
  5. Distance / Offshore Proximity (10 – 50 km ideal operational band)
  6. Optional INCOIS Bulletin Alignment
"""

from __future__ import annotations

import math
from typing import Any, Optional


def calculate_candidate_score(
    *,
    candidate_lat: float,
    candidate_lon: float,
    target_lat: float,
    target_lon: float,
    sst_val: Optional[float] = None,
    sst_grad: Optional[float] = None,
    chl_val: Optional[float] = None,
    chl_grad: Optional[float] = None,
    incois_bulletin: Optional[dict[str, Any]] = None,
    weights: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """
    Calculate deterministic multi-factor PFZ score for a single geographic candidate point.
    Returns composite score (0.0 to 1.0) alongside explicit factor components.
    """
    if weights is None:
        weights = {
            "sst_suitability": 0.25,
            "sst_front": 0.30,
            "chlorophyll": 0.20,
            "chlorophyll_gradient": 0.15,
            "distance": 0.10,
        }

    # 1. Offshore / Distance Factor
    dlat = (candidate_lat - target_lat) * 111.0
    dlon = (candidate_lon - target_lon) * 111.0 * math.cos(math.radians(target_lat))
    distance_km = math.hypot(dlat, dlon)

    # Optimal operational distance: 10 - 50 km (penalty if too far >80km or too shallow <3km)
    if distance_km < 3.0:
        f_dist = 0.4
    elif distance_km <= 50.0:
        f_dist = max(0.5, 1.0 - (distance_km / 100.0))
    else:
        f_dist = max(0.0, 1.0 - (distance_km / 80.0))

    # 2. SST Suitability Factor (Optimal 26°C - 29°C, peak at 27.5°C)
    if sst_val is not None and not math.isnan(sst_val):
        f_sst = max(0.0, 1.0 - abs(sst_val - 27.5) / 3.5)
    else:
        f_sst = None

    # 3. SST Front Factor (Grad >= 0.05 °C/km)
    if sst_grad is not None and not math.isnan(sst_grad):
        f_front = min(1.0, sst_grad / 0.12)
    else:
        f_front = None

    # 4. Chlorophyll Concentration Factor (Optimal 0.2 - 2.0 mg/m^3)
    if chl_val is not None and not math.isnan(chl_val) and chl_val > 0:
        f_chl = min(1.0, chl_val / 1.5)
    else:
        f_chl = None

    # 5. Chlorophyll Gradient Factor
    if chl_grad is not None and not math.isnan(chl_grad):
        f_chl_grad = min(1.0, chl_grad / 0.03)
    else:
        f_chl_grad = None

    # 6. Optional INCOIS Bulletin Alignment
    incois_alignment = None
    if incois_bulletin and incois_bulletin.get("status") == "ACTIVE":
        bulletin_pts = incois_bulletin.get("bulletin_candidates", [])
        for pt in bulletin_pts:
            plat = pt.get("latitude")
            plon = pt.get("longitude")
            if plat is not None and plon is not None:
                p_dist = math.hypot((candidate_lat - plat) * 111.0, (candidate_lon - plon) * 106.0)
                if p_dist <= 15.0:
                    incois_alignment = 1.0
                    break

    # Calculate weighted average over valid (non-None) factors
    factors_map = {
        "sst_suitability": f_sst,
        "sst_front": f_front,
        "chlorophyll": f_chl,
        "chlorophyll_gradient": f_chl_grad,
        "distance": f_dist,
    }

    total_score = 0.0
    total_weight = 0.0

    for factor_key, factor_val in factors_map.items():
        if factor_val is not None:
            w = weights.get(factor_key, 0.2)
            total_score += factor_val * w
            total_weight += w

    if incois_alignment is not None:
        total_score += incois_alignment * 0.20
        total_weight += 0.20

    composite_score = (total_score / total_weight) if total_weight > 0 else 0.0
    composite_score = round(min(1.0, max(0.0, composite_score)), 3)

    return {
        "latitude": round(candidate_lat, 4),
        "longitude": round(candidate_lon, 4),
        "distance_km": round(distance_km, 1),
        "score": composite_score,
        "sst_c": round(sst_val, 2) if sst_val is not None else None,
        "sst_gradient_c_per_km": round(sst_grad, 4) if sst_grad is not None else None,
        "chlorophyll_mg_m3": round(chl_val, 3) if chl_val is not None else None,
        "chlorophyll_gradient": round(chl_grad, 4) if chl_grad is not None else None,
        "factors": {
            "sst_suitability": round(f_sst, 3) if f_sst is not None else None,
            "sst_front": round(f_front, 3) if f_front is not None else None,
            "chlorophyll": round(f_chl, 3) if f_chl is not None else None,
            "chlorophyll_gradient": round(f_chl_grad, 3) if f_chl_grad is not None else None,
            "distance": round(f_dist, 3),
            "incois_alignment": incois_alignment,
        },
    }
