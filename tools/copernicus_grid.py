from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import copernicusmarine
import numpy as np


# ============================================================
# ORCA — COPERNICUS GRID SERVICE
# ============================================================
#
# Purpose:
#   Retrieve real Copernicus Marine gridded data for
#   visualization, analytics and future ML pipelines.
#
# Supported parameters:
#
#   SST
#   ocean currents
#   waves
#
# Output:
#
#   {
#       parameter,
#       unit,
#       latitudes,
#       longitudes,
#       values,
#       observation_time,
#       dataset_id
#   }
#
# This is numerical data.
#
# Flutter / map rendering will be implemented later.
#
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

CHLOROPHYLL_DATASET = (
    "cmems_mod_glo_bgc-bio_anfc_0.25deg_P1D-m"
)


SURFACE_DEPTH = 0.49402499198913574


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_value(value: Any) -> Any:

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float) and np.isnan(value):
        return None

    return value


def serialize_array(
    values: np.ndarray,
) -> list:

    array = np.asarray(values)

    return array.tolist()


# ============================================================
# OPEN GRID
# ============================================================

def open_grid_dataset(
    *,
    dataset_id: str,
    variables: list[str],
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
    hours_back: int,
    surface_data: bool = False,
):
    """
    Retrieve a bounded spatial-temporal Copernicus grid.

    Keep requested bounding boxes reasonably small.
    """

    end_time = utc_now()

    start_time = (
        end_time -
        timedelta(hours=hours_back)
    )

    request: dict[str, Any] = {

        "dataset_id":
            dataset_id,

        "variables":
            variables,

        "minimum_latitude":
            minimum_latitude,

        "maximum_latitude":
            maximum_latitude,

        "minimum_longitude":
            minimum_longitude,

        "maximum_longitude":
            maximum_longitude,

        "start_datetime":
            start_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),

        "end_datetime":
            end_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
    }


    if surface_data:

        request[
            "minimum_depth"
        ] = SURFACE_DEPTH

        request[
            "maximum_depth"
        ] = SURFACE_DEPTH


    return copernicusmarine.open_dataset(
        **request
    )


# ============================================================
# SELECT LATEST TIME + SURFACE
# ============================================================

def select_latest_surface(
    data_array,
):
    """
    Select surface level and latest available
    temporal field.
    """

    data = data_array


    # --------------------------------------------------------
    # SURFACE
    # --------------------------------------------------------

    if "depth" in data.dims:

        data = data.sel(
            depth=SURFACE_DEPTH,
            method="nearest",
        )


    # --------------------------------------------------------
    # LATEST TIME
    # --------------------------------------------------------

    observation_time = None

    if "time" in data.dims:

        data = data.sortby(
            "time"
        )

        data = data.isel(
            time=-1
        )

        if "time" in data.coords:

            observation_time = str(
                data.coords[
                    "time"
                ].values
            )


    return data.squeeze(), observation_time


# ============================================================
# SST GRID
# ============================================================

def get_sst_grid(
    *,
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
) -> dict[str, Any]:

    dataset = open_grid_dataset(

        dataset_id=
            TEMPERATURE_DATASET,

        variables=[
            "thetao"
        ],

        minimum_latitude=
            minimum_latitude,

        maximum_latitude=
            maximum_latitude,

        minimum_longitude=
            minimum_longitude,

        maximum_longitude=
            maximum_longitude,

        hours_back=72,

        surface_data=True,
    )


    data, observation_time = (
        select_latest_surface(
            dataset["thetao"]
        )
    )


    values = np.asarray(
        data.values,
        dtype=np.float32,
    )


    latitudes = (
        data.coords[
            "latitude"
        ].values
    )

    longitudes = (
        data.coords[
            "longitude"
        ].values
    )


    return {

        "parameter":
            "sea_surface_temperature",

        "short_name":
            "sst",

        "unit":
            "degC",

        "status":
            "OBSERVED",

        "observation_time":
            observation_time,

        "dataset_id":
            TEMPERATURE_DATASET,

        "latitudes":
            serialize_array(
                latitudes
            ),

        "longitudes":
            serialize_array(
                longitudes
            ),

        "values":
            serialize_array(
                values
            ),

        "shape":
            list(values.shape),
    }


# ============================================================
# CURRENT GRID
# ============================================================

def get_current_grid(
    *,
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
) -> dict[str, Any]:

    dataset = open_grid_dataset(

        dataset_id=
            CURRENT_DATASET,

        variables=[
            "uo",
            "vo",
        ],

        minimum_latitude=
            minimum_latitude,

        maximum_latitude=
            maximum_latitude,

        minimum_longitude=
            minimum_longitude,

        maximum_longitude=
            maximum_longitude,

        hours_back=72,

        surface_data=True,
    )


    u, observation_time = (
        select_latest_surface(
            dataset["uo"]
        )
    )

    v, _ = (
        select_latest_surface(
            dataset["vo"]
        )
    )


    u_values = np.asarray(
        u.values,
        dtype=np.float32,
    )

    v_values = np.asarray(
        v.values,
        dtype=np.float32,
    )


    # --------------------------------------------------------
    # SPEED
    # --------------------------------------------------------

    speed = np.sqrt(
        u_values ** 2 +
        v_values ** 2
    )


    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------
    #
    # Direction toward which current flows.
    #
    # Clockwise from north.
    #
    # --------------------------------------------------------

    direction = (
        np.degrees(
            np.arctan2(
                u_values,
                v_values,
            )
        )
        + 360.0
    ) % 360.0


    latitudes = (
        u.coords[
            "latitude"
        ].values
    )

    longitudes = (
        u.coords[
            "longitude"
        ].values
    )


    return {

        "parameter":
            "ocean_current",

        "short_name":
            "current",

        "status":
            "OBSERVED",

        "observation_time":
            observation_time,

        "dataset_id":
            CURRENT_DATASET,

        "components": {

            "u": {
                "unit": "m/s",

                "values":
                    serialize_array(
                        u_values
                    ),
            },

            "v": {
                "unit": "m/s",

                "values":
                    serialize_array(
                        v_values
                    ),
            },
        },

        "speed": {

            "unit": "m/s",

            "values":
                serialize_array(
                    speed
                ),
        },

        "direction": {

            "unit": "degree",

            "values":
                serialize_array(
                    direction
                ),
        },

        "latitudes":
            serialize_array(
                latitudes
            ),

        "longitudes":
            serialize_array(
                longitudes
            ),

        "shape":
            list(
                speed.shape
            ),
    }


# ============================================================
# WAVE GRID
# ============================================================

def get_wave_grid(
    *,
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
) -> dict[str, Any]:

    dataset = open_grid_dataset(

        dataset_id=
            WAVE_DATASET,

        variables=[
            "VHM0",
            "VTM02",
            "VMDR",
        ],

        minimum_latitude=
            minimum_latitude,

        maximum_latitude=
            maximum_latitude,

        minimum_longitude=
            minimum_longitude,

        maximum_longitude=
            maximum_longitude,

        hours_back=48,

        surface_data=False,
    )


    wave_height, observation_time = (
        select_latest_surface(
            dataset["VHM0"]
        )
    )

    wave_period, _ = (
        select_latest_surface(
            dataset["VTM02"]
        )
    )

    wave_direction, _ = (
        select_latest_surface(
            dataset["VMDR"]
        )
    )


    height_values = np.asarray(
        wave_height.values,
        dtype=np.float32,
    )

    period_values = np.asarray(
        wave_period.values,
        dtype=np.float32,
    )

    direction_values = np.asarray(
        wave_direction.values,
        dtype=np.float32,
    )


    latitudes = (
        wave_height.coords[
            "latitude"
        ].values
    )

    longitudes = (
        wave_height.coords[
            "longitude"
        ].values
    )


    return {

        "parameter":
            "waves",

        "short_name":
            "waves",

        "status":
            "OBSERVED",

        "observation_time":
            observation_time,

        "dataset_id":
            WAVE_DATASET,

        "significant_wave_height": {

            "unit": "m",

            "values":
                serialize_array(
                    height_values
                ),
        },

        "mean_wave_period": {

            "unit": "s",

            "values":
                serialize_array(
                    period_values
                ),
        },

        "wave_direction": {

            "unit": "degree",

            "values":
                serialize_array(
                    direction_values
                ),
        },

        "latitudes":
            serialize_array(
                latitudes
            ),

        "longitudes":
            serialize_array(
                longitudes
            ),

        "shape":
            list(
                height_values.shape
            ),
    }


# ============================================================
# CHLOROPHYLL GRID
# ============================================================

def get_chlorophyll_grid(
    *,
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
) -> dict[str, Any]:

    dataset = open_grid_dataset(

        dataset_id=
            CHLOROPHYLL_DATASET,

        variables=[
            "chl"
        ],

        minimum_latitude=
            minimum_latitude,

        maximum_latitude=
            maximum_latitude,

        minimum_longitude=
            minimum_longitude,

        maximum_longitude=
            maximum_longitude,

        hours_back=72,

        surface_data=True,
    )


    data, observation_time = (
        select_latest_surface(
            dataset["chl"]
        )
    )


    values = np.asarray(
        data.values,
        dtype=np.float32,
    )


    latitudes = (
        data.coords[
            "latitude"
        ].values
    )

    longitudes = (
        data.coords[
            "longitude"
        ].values
    )


    return {

        "parameter":
            "chlorophyll_a",

        "short_name":
            "chlorophyll",

        "unit":
            "mg/m3",

        "status":
            "MODEL_ANALYSIS",

        "observation_time":
            observation_time,

        "dataset_id":
            CHLOROPHYLL_DATASET,

        "latitudes":
            serialize_array(
                latitudes
            ),

        "longitudes":
            serialize_array(
                longitudes
            ),

        "values":
            serialize_array(
                values
            ),

        "shape":
            list(values.shape),
    }


# ============================================================
# GENERIC GRID FUNCTION
# ============================================================

def get_copernicus_grid(
    parameter: str,
    *,
    minimum_latitude: float,
    maximum_latitude: float,
    minimum_longitude: float,
    maximum_longitude: float,
) -> dict[str, Any]:

    parameter = parameter.lower().strip()


    if parameter in {
        "sst",
        "temperature",
        "sea_surface_temperature",
    }:

        return get_sst_grid(

            minimum_latitude=
                minimum_latitude,

            maximum_latitude=
                maximum_latitude,

            minimum_longitude=
                minimum_longitude,

            maximum_longitude=
                maximum_longitude,
        )


    if parameter in {
        "current",
        "currents",
        "ocean_current",
    }:

        return get_current_grid(

            minimum_latitude=
                minimum_latitude,

            maximum_latitude=
                maximum_latitude,

            minimum_longitude=
                minimum_longitude,

            maximum_longitude=
                maximum_longitude,
        )


    if parameter in {
        "wave",
        "waves",
    }:

        return get_wave_grid(

            minimum_latitude=
                minimum_latitude,

            maximum_latitude=
                maximum_latitude,

            minimum_longitude=
                minimum_longitude,

            maximum_longitude=
                maximum_longitude,
        )


    if parameter in {
        "chlorophyll",
        "chlorophyll_a",
        "chl",
    }:

        return get_chlorophyll_grid(

            minimum_latitude=
                minimum_latitude,

            maximum_latitude=
                maximum_latitude,

            minimum_longitude=
                minimum_longitude,

            maximum_longitude=
                maximum_longitude,
        )


    raise ValueError(

        f"Unsupported parameter: {parameter}. "

        "Supported parameters: "
        "sst, currents, waves, chlorophyll."
    )