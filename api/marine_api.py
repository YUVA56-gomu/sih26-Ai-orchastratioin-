from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from tools.copernicus_service import (
    get_copernicus_marine_snapshot,
)

from tools.copernicus_grid import (
    get_copernicus_grid,
)

from tools.copernicus_wmts import (
    discover_layers,
    discover_orca_layers,
    get_capabilities_xml,
    build_orca_tile_template,
    build_orca_legend_url,
    get_orca_wmts_layer,
)


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="ORCA Marine Data Gateway",
    version="0.2.0",
    description=(
        "Local gateway for Copernicus Marine numerical "
        "data and WMTS map layers."
    ),
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:

    return {
        "service":
            "ORCA Marine Data Gateway",

        "version":
            "0.2.0",

        "status":
            "online",

        "endpoints": {
            "health":
                "/health",

            "point":
                "/marine/point",

            "grid":
                "/marine/grid",

            "capabilities":
                "/marine/map/capabilities",

            "layers":
                "/marine/map/layers",

            "orca_layers":
                "/marine/map/orca-layers",

            "map_config":
                "/marine/map/config/{parameter}",
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health() -> dict[str, str]:

    return {
        "status": "ok",
        "service":
            "orca-marine-data-gateway",
    }


# ============================================================
# POINT DATA
# ============================================================

@app.get("/marine/point")
def marine_point(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
) -> dict[str, Any]:

    try:

        return (
            get_copernicus_marine_snapshot(
                latitude=latitude,
                longitude=longitude,
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "Copernicus data retrieval failed",

                "message":
                    str(exc),
            },
        )


# ============================================================
# GRID DATA
# ============================================================

@app.get("/marine/grid")
def marine_grid(
    parameter: str = Query(
        ...,
        description=(
            "Supported values: "
            "sst, currents, waves"
        ),
    ),

    minimum_latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),

    maximum_latitude: float = Query(
        ...,
        ge=-90,
        le=90,
    ),

    minimum_longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),

    maximum_longitude: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
) -> dict[str, Any]:

    if minimum_latitude >= maximum_latitude:

        raise HTTPException(
            status_code=400,
            detail=(
                "minimum_latitude must be "
                "less than maximum_latitude"
            ),
        )

    if minimum_longitude >= maximum_longitude:

        raise HTTPException(
            status_code=400,
            detail=(
                "minimum_longitude must be "
                "less than maximum_longitude"
            ),
        )

    try:

        return get_copernicus_grid(
            parameter,
            minimum_latitude=minimum_latitude,
            maximum_latitude=maximum_latitude,
            minimum_longitude=minimum_longitude,
            maximum_longitude=maximum_longitude,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "Copernicus grid retrieval failed",

                "message":
                    str(exc),
            },
        )


# ============================================================
# WMTS CAPABILITIES
# ============================================================

@app.get(
    "/marine/map/capabilities",
    response_class=Response,
)
def wmts_capabilities() -> Response:

    try:

        xml = get_capabilities_xml()

        return Response(
            content=xml,
            media_type="application/xml",
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "Copernicus WMTS capabilities failed",

                "message":
                    str(exc),
            },
        )


# ============================================================
# WMTS LAYERS
# ============================================================

@app.get("/marine/map/layers")
def wmts_layers() -> dict[str, Any]:

    try:

        layers = discover_layers()

        return {
            "service":
                "Copernicus Marine WMTS",

            "endpoint":
                "https://wmts.marine.copernicus.eu/teroWmts",

            "count":
                len(layers),

            "layers":
                layers,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "WMTS layer discovery failed",

                "message":
                    str(exc),
            },
        )


# ============================================================
# ORCA CATEGORIZED LAYERS
# ============================================================

@app.get("/marine/map/orca-layers")
def orca_map_layers() -> dict[str, Any]:

    try:

        layers = discover_layers()

        categorized = (
            discover_orca_layers(
                layers
            )
        )

        return {
            "service":
                "Copernicus Marine WMTS",

            "endpoint":
                "https://wmts.marine.copernicus.eu/teroWmts",

            "count":
                len(layers),

            "categories":
                categorized,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "Copernicus WMTS discovery failed",

                "message":
                    str(exc),
            },
        )


# ============================================================
# MAP CONFIGURATION
# ============================================================

@app.get(
    "/marine/map/config/{parameter}"
)
def map_config(
    parameter: str,
) -> dict[str, Any]:

    parameter = (
        parameter
        .lower()
        .strip()
    )

    try:

        definition = (
            get_orca_wmts_layer(
                parameter
            )
        )

        tile_url = (
            build_orca_tile_template(
                parameter
            )
        )

        legend_url = (
            build_orca_legend_url(
                parameter
            )
        )

        return {
            "parameter":
                parameter,

            "title":
                definition["title"],

            "unit":
                definition["unit"],

            "layer":
                definition["layer"],

            "projection":
                "EPSG:3857",

            "tile_matrix_set":
                definition["matrix_set"],

            "tile_size":
                256,

            "tile_url":
                tile_url,

            "legend_url":
                legend_url,

            "style":
                definition["style"],

            "source":
                "Copernicus Marine WMTS",
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail={
                "error":
                    "Map configuration failed",

                "message":
                    str(exc),
            },
        )