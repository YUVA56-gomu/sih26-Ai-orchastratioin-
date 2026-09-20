"""
tools/pfz_fronts.py
───────────────────
Deterministic numerical analysis for Thermal Front Detection (SST)
and Ocean Productivity Analysis (Chlorophyll-a).

Implements spatial gradient calculations (numpy.gradient) converted
to physical distances (°C/km or mg/m^3/km) taking latitude into account.
"""

from __future__ import annotations

from typing import Any
import numpy as np

# Configurable thresholds
DEFAULT_SST_FRONT_THRESHOLD_C_PER_KM = 0.05
DEFAULT_CHL_GRADIENT_THRESHOLD = 0.01


def calculate_spatial_gradient(
    values: np.ndarray,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate 2D spatial gradient magnitude and direction.
    Converts grid step sizes into physical kilometers accounting for latitude.
    """
    val_arr = np.asarray(values, dtype=np.float64)
    lats = np.asarray(latitudes, dtype=np.float64)
    lons = np.asarray(longitudes, dtype=np.float64)

    if val_arr.ndim != 2 or len(lats) < 2 or len(lons) < 2:
        empty = np.zeros_like(val_arr)
        return empty, empty, empty

    dlat_deg = float(np.abs(lats[1] - lats[0])) if len(lats) > 1 else 0.083
    dlon_deg = float(np.abs(lons[1] - lons[0])) if len(lons) > 1 else 0.083

    mean_lat_rad = np.radians(np.mean(lats))
    dy_km = max(0.1, dlat_deg * 111.0)
    dx_km = max(0.1, dlon_deg * 111.0 * np.cos(mean_lat_rad))

    # numpy.gradient: axis 0 is rows (lat), axis 1 is cols (lon)
    grad_y, grad_x = np.gradient(val_arr, dy_km, dx_km)

    magnitude = np.sqrt(grad_y**2 + grad_x**2)

    # Direction in degrees clockwise from North
    direction = (np.degrees(np.arctan2(grad_x, grad_y)) + 360.0) % 360.0

    return magnitude, direction, grad_y


def detect_thermal_fronts(
    sst_grid: dict[str, Any],
    min_gradient_c_per_km: float = DEFAULT_SST_FRONT_THRESHOLD_C_PER_KM,
) -> list[dict[str, Any]]:
    """
    Detect thermal fronts from an SST grid dict.
    Returns list of candidate front features with location, gradient, and strength.
    """
    if not isinstance(sst_grid, dict) or "values" not in sst_grid:
        return []

    lats = sst_grid.get("latitudes", [])
    lons = sst_grid.get("longitudes", [])
    raw_vals = sst_grid.get("values", [])

    if len(lats) == 0 or len(lons) == 0 or len(raw_vals) == 0:
        return []

    val_arr = np.asarray(raw_vals, dtype=np.float64)

    # If flattened, reshape using latitudes/longitudes
    if val_arr.ndim == 1:
        if len(lats) * len(lons) == val_arr.size:
            val_arr = val_arr.reshape((len(lats), len(lons)))
        else:
            return []

    magnitude, direction, _ = calculate_spatial_gradient(val_arr, np.asarray(lats), np.asarray(lons))

    fronts = []
    rows, cols = val_arr.shape

    for r in range(rows):
        for c in range(cols):
            mag = float(magnitude[r, c])
            if not np.isnan(mag) and mag >= min_gradient_c_per_km:
                front_strength = min(1.0, mag / 0.15)
                fronts.append({
                    "latitude": round(float(lats[r]), 4),
                    "longitude": round(float(lons[c]), 4),
                    "gradient_c_per_km": round(mag, 4),
                    "gradient_direction_deg": round(float(direction[r, c]), 1),
                    "front_strength": round(front_strength, 3),
                    "sst_c": round(float(val_arr[r, c]), 2) if not np.isnan(val_arr[r, c]) else None,
                })

    # Sort descending by front strength
    fronts.sort(key=lambda x: x["front_strength"], reverse=True)
    return fronts


def analyze_chlorophyll_productivity(
    chl_grid: dict[str, Any],
    min_gradient: float = DEFAULT_CHL_GRADIENT_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Analyze chlorophyll-a grid for ocean productivity signals and productivity gradients.
    """
    if not isinstance(chl_grid, dict) or "values" not in chl_grid:
        return []

    lats = chl_grid.get("latitudes", [])
    lons = chl_grid.get("longitudes", [])
    raw_vals = chl_grid.get("values", [])

    if len(lats) == 0 or len(lons) == 0 or len(raw_vals) == 0:
        return []

    val_arr = np.asarray(raw_vals, dtype=np.float64)

    if val_arr.ndim == 1:
        if len(lats) * len(lons) == val_arr.size:
            val_arr = val_arr.reshape((len(lats), len(lons)))
        else:
            return []

    magnitude, _, _ = calculate_spatial_gradient(val_arr, np.asarray(lats), np.asarray(lons))

    features = []
    rows, cols = val_arr.shape

    for r in range(rows):
        for c in range(cols):
            chl_val = float(val_arr[r, c])
            if np.isnan(chl_val) or chl_val <= 0:
                continue

            grad_mag = float(magnitude[r, c])
            if np.isnan(grad_mag):
                grad_mag = 0.0

            # Signal strength based on chlorophyll range (optimal 0.2 - 2.0 mg/m^3)
            signal = min(1.0, max(0.0, chl_val / 1.5))

            if chl_val >= 0.15 or grad_mag >= min_gradient:
                features.append({
                    "latitude": round(float(lats[r]), 4),
                    "longitude": round(float(lons[c]), 4),
                    "chlorophyll_mg_m3": round(chl_val, 3),
                    "chlorophyll_gradient": round(grad_mag, 4),
                    "productivity_signal": round(signal, 3),
                })

    features.sort(key=lambda x: (x["productivity_signal"], x["chlorophyll_gradient"]), reverse=True)
    return features
