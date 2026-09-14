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

TEMPERATURE_DATASET = (
    "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m"
)

CURRENT_DATASET = (
    "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"
)

WAVE_DATASET = (
    "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i"
)


# ============================================================
# DATASET SURFACE
# ============================================================

SURFACE_DEPTH = 0.49402499198913574


# ============================================================
# REQUEST WINDOWS
# ============================================================

TEMPERATURE_LOOKBACK_HOURS = 72
CURRENT_LOOKBACK_HOURS = 72
WAVE_LOOKBACK_HOURS = 48

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
    # Surface depth
    # --------------------------------------------------------

    if "depth" in data.dims:

        data = data.sel(
            depth=SURFACE_DEPTH,
            method="nearest",
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


    return {
        "value": value,
        "observation_time": observation_time,
    }


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

        "currents":
            get_currents,

        "waves":
            get_waves,
    }


    with ThreadPoolExecutor(
        max_workers=3
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


    if available == 3:

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