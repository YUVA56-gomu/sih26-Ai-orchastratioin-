from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import copernicusmarine
import numpy as np


# ============================================================
# ORCA — COPERNICUS MARINE DATA SERVICE
# ============================================================
#
# Real numerical observations from Copernicus Marine.
#
# Current parameters:
#
#   SST
#   Ocean currents
#   Waves
#
# Design goals:
#
#   1. Small geographic requests
#   2. Small temporal windows
#   3. Parallel parameter retrieval
#   4. JSON-safe output
#   5. Provenance
#   6. Observation timestamps
#   7. Explicit OBSERVED status
#   8. Partial-failure tolerance
#   9. Small cache for repeated queries
#
# ============================================================


# ============================================================
# DATASETS
# ============================================================

SALINITY_DATASET = (
    "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m"
)

TEMPERATURE_DATASET = (
    "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m"
)

CURRENT_DATASET = (
    "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"
)

WAVE_DATASET = (
    "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i"
)

CHLOROPHYLL_DATASET = (
    "cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m"
)


# ============================================================
# DATASET SURFACE
# ============================================================

SURFACE_DEPTH = 0.49402499198913574


# ============================================================
# REQUEST WINDOWS
# ============================================================

SALINITY_LOOKBACK_HOURS = 72
TEMPERATURE_LOOKBACK_HOURS = 72
CURRENT_LOOKBACK_HOURS = 72
WAVE_LOOKBACK_HOURS = 48
CHLOROPHYLL_LOOKBACK_HOURS = 72

POINT_WINDOW_DEGREES = 0.05


# ============================================================
# CACHE
# ============================================================

CACHE_TTL_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def json_value(value: Any) -> Any:
    """
    Convert NumPy values into JSON-safe Python types.
    """

    if value is None:
        return None

    if isinstance(value, np.ndarray):

        if value.size == 1:
            value = value.item()

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float) and np.isnan(value):
        return None

    return value


# ============================================================
# COPERNICUS DATASET ACCESS
# ============================================================

def open_small_dataset(
    *,
    dataset_id: str,
    variables: list[str],
    latitude: float,
    longitude: float,
    hours_back: int,
    surface_data: bool = False,
):
    """
    Open a deliberately small Copernicus spatial/time slice.
    """

    end_time = utc_now()

    start_time = (
        end_time -
        timedelta(hours=hours_back)
    )

    request: dict[str, Any] = {

        "dataset_id": dataset_id,

        "variables": variables,

        "minimum_longitude": (
            longitude -
            POINT_WINDOW_DEGREES
        ),

        "maximum_longitude": (
            longitude +
            POINT_WINDOW_DEGREES
        ),

        "minimum_latitude": (
            latitude -
            POINT_WINDOW_DEGREES
        ),

        "maximum_latitude": (
            latitude +
            POINT_WINDOW_DEGREES
        ),

        "start_datetime": (
            start_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
        ),

        "end_datetime": (
            end_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
        ),
    }

    if surface_data:

        request["minimum_depth"] = SURFACE_DEPTH
        request["maximum_depth"] = SURFACE_DEPTH

    return copernicusmarine.open_dataset(
        **request
    )


# ============================================================
# EXTRACT LATEST VALUE
# ============================================================

def latest_value(
    dataset,
    variable: str,
    latitude: float,
    longitude: float,
    depth: float | None = None,
) -> dict[str, Any]:

    if variable not in dataset:

        raise KeyError(
            f"Variable '{variable}' not found. "
            f"Available variables: "
            f"{list(dataset.data_vars)}"
        )

    data = dataset[variable]


    # --------------------------------------------------------
    # Horizontal nearest point
    # --------------------------------------------------------

    if "latitude" in data.coords:

        data = data.sel(
            latitude=latitude,
            method="nearest",
        )


    if "longitude" in data.coords:

        data = data.sel(
            longitude=longitude,
            method="nearest",
        )


    # --------------------------------------------------------
    # Depth selection (surface vs requested depth level)
    # --------------------------------------------------------

    actual_depth = None

    if depth is not None:

        if "depth" in data.dims or "depth" in data.coords:

            data = data.sel(
                depth=depth,
                method="nearest",
            )

            if "depth" in data.coords:

                actual_depth = json_value(
                    data.coords["depth"].values
                )

    elif "depth" in data.dims or "depth" in data.coords:

        data = data.sel(
            depth=SURFACE_DEPTH,
            method="nearest",
        )

        if "depth" in data.coords:

            actual_depth = json_value(
                data.coords["depth"].values
            )


    # --------------------------------------------------------
    # Latest available time
    # --------------------------------------------------------

    observation_time = None

    if "time" in data.dims:

        data = data.sortby("time")

        data = data.isel(
            time=-1
        )

        if "time" in data.coords:

            observation_time = str(
                data.coords["time"].values
            )


    data = data.squeeze()

    value = json_value(
        data.values
    )


    res = {
        "value": value,
        "observation_time": observation_time,
    }

    if actual_depth is not None:

        res["depth"] = actual_depth

    return res


# ============================================================
# SST
# ============================================================

def get_temperature(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    dataset = open_small_dataset(

        dataset_id=TEMPERATURE_DATASET,

        variables=[
            "thetao"
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            TEMPERATURE_LOOKBACK_HOURS
        ),

        surface_data=True,
    )


    result = latest_value(

        dataset,

        "thetao",

        latitude,
        longitude,
    )


    return {

        "parameter":
            "sea_surface_temperature",

        "value":
            result["value"],

        "unit":
            "degC",

        "variable":
            "thetao",

        "status":
            "OBSERVED",

        "observation_time":
            result["observation_time"],

        "dataset_id":
            TEMPERATURE_DATASET,
    }


# ============================================================
# OCEAN CURRENTS
# ============================================================

def get_currents(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    dataset = open_small_dataset(

        dataset_id=CURRENT_DATASET,

        variables=[
            "uo",
            "vo",
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            CURRENT_LOOKBACK_HOURS
        ),

        surface_data=True,
    )


    u_result = latest_value(

        dataset,

        "uo",

        latitude,
        longitude,
    )


    v_result = latest_value(

        dataset,

        "vo",

        latitude,
        longitude,
    )


    u = u_result["value"]
    v = v_result["value"]

    speed = None
    direction = None


    if u is not None and v is not None:

        u = float(u)
        v = float(v)

        speed = float(
            np.sqrt(
                (u * u) +
                (v * v)
            )
        )

        # Direction toward which
        # the current is flowing.

        direction = float(
            (
                np.degrees(
                    np.arctan2(
                        u,
                        v,
                    )
                )
                + 360.0
            )
            % 360.0
        )


    return {

        "parameter":
            "ocean_current",

        "u_ms":
            u,

        "v_ms":
            v,

        "speed_ms":
            speed,

        "direction_deg":
            direction,

        "speed_unit":
            "m/s",

        "direction_unit":
            "degree",

        "variables": [
            "uo",
            "vo",
        ],

        "status":
            "OBSERVED",

        "observation_time":
            u_result[
                "observation_time"
            ],

        "dataset_id":
            CURRENT_DATASET,
    }


# ============================================================
# WAVES
# ============================================================

def get_waves(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    dataset = open_small_dataset(

        dataset_id=WAVE_DATASET,

        variables=[
            "VHM0",
            "VTM02",
            "VMDR",
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            WAVE_LOOKBACK_HOURS
        ),

        surface_data=False,
    )


    height_result = latest_value(

        dataset,

        "VHM0",

        latitude,
        longitude,
    )


    period_result = latest_value(

        dataset,

        "VTM02",

        latitude,
        longitude,
    )


    direction_result = latest_value(

        dataset,

        "VMDR",

        latitude,
        longitude,
    )


    return {

        "parameter":
            "waves",

        "significant_wave_height_m":
            height_result[
                "value"
            ],

        "mean_wave_period_s":
            period_result[
                "value"
            ],

        "wave_direction_deg":
            direction_result[
                "value"
            ],

        "variables": [
            "VHM0",
            "VTM02",
            "VMDR",
        ],

        "status":
            "OBSERVED",

        "observation_time":
            height_result[
                "observation_time"
            ],

        "dataset_id":
            WAVE_DATASET,
    }


# ============================================================
# SALINITY
# ============================================================

def get_salinity(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    dataset = open_small_dataset(

        dataset_id=SALINITY_DATASET,

        variables=[
            "so"
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            SALINITY_LOOKBACK_HOURS
        ),

        surface_data=True,
    )


    result = latest_value(

        dataset,

        "so",

        latitude,
        longitude,
    )


    return {

        "parameter":
            "sea_water_salinity",

        "value":
            result["value"],

        "unit":
            "psu",

        "variable":
            "so",

        "latitude":
            latitude,

        "longitude":
            longitude,

        "status":
            "OBSERVED",

        "observation_time":
            result["observation_time"],

        "dataset_id":
            SALINITY_DATASET,
    }


# ============================================================
# CURRENT VELOCITY PROFILES
# ============================================================

def get_current_profile(
    latitude: float,
    longitude: float,
    target_depths: list[float] | None = None,
) -> dict[str, Any]:

    if target_depths is None:

        target_depths = [
            0.49,
            9.57,
            21.6,
            51.9,
        ]


    dataset = open_small_dataset(

        dataset_id=CURRENT_DATASET,

        variables=[
            "uo",
            "vo",
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            CURRENT_LOOKBACK_HOURS
        ),

        surface_data=False,
    )


    profile_levels = []

    obs_time = None


    for target_d in target_depths:

        try:

            u_res = latest_value(
                dataset,
                "uo",
                latitude,
                longitude,
                depth=target_d,
            )

            v_res = latest_value(
                dataset,
                "vo",
                latitude,
                longitude,
                depth=target_d,
            )


            u = u_res["value"]
            v = v_res["value"]

            actual_d = u_res.get(
                "depth",
                target_d,
            )


            if obs_time is None:

                obs_time = u_res.get(
                    "observation_time"
                )


            speed = None

            direction = None


            if u is not None and v is not None:

                u = float(u)
                v = float(v)

                speed = float(
                    np.sqrt(
                        (u * u) +
                        (v * v)
                    )
                )

                direction = float(
                    (
                        np.degrees(
                            np.arctan2(
                                u,
                                v,
                            )
                        )
                        + 360.0
                    )
                    % 360.0
                )


            profile_levels.append({

                "requested_depth_m":
                    target_d,

                "depth_m":
                    actual_d,

                "u_ms":
                    u,

                "v_ms":
                    v,

                "speed_ms":
                    speed,

                "direction_deg":
                    direction,
            })


        except Exception:

            continue


    return {

        "parameter":
            "ocean_current_profile",

        "profile":
            profile_levels,

        "speed_unit":
            "m/s",

        "direction_unit":
            "degree",

        "depth_unit":
            "m",

        "variables": [
            "uo",
            "vo",
        ],

        "latitude":
            latitude,

        "longitude":
            longitude,

        "status":
            "OBSERVED",

        "observation_time":
            obs_time,

        "dataset_id":
            CURRENT_DATASET,
    }


# ============================================================
# CHLOROPHYLL-A
# ============================================================

def get_chlorophyll(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:

    dataset = open_small_dataset(

        dataset_id=CHLOROPHYLL_DATASET,

        variables=[
            "chl"
        ],

        latitude=latitude,
        longitude=longitude,

        hours_back=(
            CHLOROPHYLL_LOOKBACK_HOURS
        ),

        surface_data=True,
    )


    result = latest_value(

        dataset,

        "chl",

        latitude,
        longitude,
    )


    return {

        "parameter":
            "chlorophyll_a",

        "value":
            result["value"],

        "unit":
            "mg/m3",

        "variable":
            "chl",

        "latitude":
            latitude,

        "longitude":
            longitude,

        "status":
            "MODEL_ANALYSIS",

        "observation_time":
            result["observation_time"],

        "dataset_id":
            CHLOROPHYLL_DATASET,
    }


# ============================================================
# CACHE
# ============================================================

_cache: dict[
    tuple[float, float],
    tuple[float, dict[str, Any]]
] = {}


def _cache_key(
    latitude: float,
    longitude: float,
) -> tuple[float, float]:

    return (
        round(latitude, 3),
        round(longitude, 3),
    )


def _get_cached(
    key: tuple[float, float],
) -> dict[str, Any] | None:

    entry = _cache.get(key)

    if entry is None:
        return None

    cached_at, value = entry

    age = (
        datetime.now(timezone.utc).timestamp()
        - cached_at
    )

    if age > CACHE_TTL_SECONDS:

        _cache.pop(key, None)

        return None

    return value


def _set_cache(
    key: tuple[float, float],
    value: dict[str, Any],
) -> None:

    _cache[key] = (
        datetime.now(
            timezone.utc
        ).timestamp(),

        value,
    )


# ============================================================
# COMPLETE SNAPSHOT
# ============================================================

def get_copernicus_marine_snapshot(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    """
    Retrieve SST, currents and waves concurrently.
    """

    latitude = float(latitude)
    longitude = float(longitude)

    cache_key = _cache_key(
        latitude,
        longitude,
    )


    cached = _get_cached(
        cache_key
    )

    if cached is not None:

        cached_copy = dict(cached)

        cached_copy[
            "cache"
        ] = {
            "hit": True,
            "ttl_seconds": (
                CACHE_TTL_SECONDS
            ),
        }

        return cached_copy


    retrieved_at = utc_now().isoformat()


    result: dict[str, Any] = {

        "source":
            "Copernicus Marine",

        "location": {

            "latitude":
                latitude,

            "longitude":
                longitude,
        },

        "retrieved_at":
            retrieved_at,

        "observations": {},

        "provenance": [],

        "warnings": [],

        "status":
            "UNKNOWN",

        "cache": {

            "hit": False,

            "ttl_seconds":
                CACHE_TTL_SECONDS,
        },
    }


    # ========================================================
    # PARALLEL DATA REQUESTS
    # ========================================================

    tasks = {

        "temperature":
            get_temperature,

        "salinity":
            get_salinity,

        "currents":
            get_currents,

        "current_profile":
            get_current_profile,

        "waves":
            get_waves,
    }


    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        futures = {

            name:
                executor.submit(
                    function,
                    latitude,
                    longitude,
                )

            for name, function
            in tasks.items()
        }


        for name, future in futures.items():

            try:

                value = future.result()

                result[
                    "observations"
                ][name] = value


            except Exception as exc:

                result[
                    "warnings"
                ].append({

                    "parameter":
                        name,

                    "error":
                        str(exc),
                })


    # ========================================================
    # PROVENANCE
    # ========================================================

    if "temperature" in result[
        "observations"
    ]:

        result[
            "provenance"
        ].append({

            "parameter":
                "sea_surface_temperature",

            "dataset_id":
                TEMPERATURE_DATASET,

            "variables":
                ["thetao"],
        })


    if "salinity" in result[
        "observations"
    ]:

        result[
            "provenance"
        ].append({

            "parameter":
                "sea_water_salinity",

            "dataset_id":
                SALINITY_DATASET,

            "variables":
                ["so"],
        })


    if "currents" in result[
        "observations"
    ]:

        result[
            "provenance"
        ].append({

            "parameter":
                "ocean_current",

            "dataset_id":
                CURRENT_DATASET,

            "variables":
                ["uo", "vo"],
        })


    if "current_profile" in result[
        "observations"
    ]:

        profile_obs = result["observations"]["current_profile"]

        result[
            "provenance"
        ].append({

            "parameter":
                "ocean_current_profile",

            "dataset_id":
                CURRENT_DATASET,

            "variables":
                ["uo", "vo"],

            "depth_levels_m": [
                p.get("depth_m")
                for p in profile_obs.get("profile", [])
                if isinstance(p, dict)
            ],
        })


    if "waves" in result[
        "observations"
    ]:

        result[
            "provenance"
        ].append({

            "parameter":
                "waves",

            "dataset_id":
                WAVE_DATASET,

            "variables":
                [
                    "VHM0",
                    "VTM02",
                    "VMDR",
                ],
        })


    # ========================================================
    # STATUS
    # ========================================================

    available = len(
        result["observations"]
    )

    failed = len(
        result["warnings"]
    )


    if available == 5:

        result[
            "status"
        ] = "COMPLETE"

    elif available > 0:

        result[
            "status"
        ] = "PARTIAL"

    else:

        result[
            "status"
        ] = "NO_DATA"


    result["summary"] = {

        "parameters_available":
            available,

        "parameters_failed":
            failed,

        "data_status":
            result["status"],
    }


    # Cache only successful/partial
    # real responses.

    if available > 0:

        _set_cache(
            cache_key,
            result,
        )


    return result