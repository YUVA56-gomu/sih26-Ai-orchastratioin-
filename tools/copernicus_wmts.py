from __future__ import annotations

from typing import Any
from urllib.parse import quote
import requests
import xml.etree.ElementTree as ET


# ============================================================
# COPERNICUS WMTS
# ============================================================

WMTS_URL = (
    "https://wmts.marine.copernicus.eu/teroWmts"
)


# ============================================================
# CAPABILITIES
# ============================================================

def get_capabilities_xml() -> str:
    response = requests.get(
        WMTS_URL,
        params={
            "SERVICE": "WMTS",
            "VERSION": "1.0.0",
            "REQUEST": "GetCapabilities",
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.text


# ============================================================
# XML HELPERS
# ============================================================

def _strip_namespace(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _text(
    element: ET.Element | None,
) -> str | None:
    if element is None:
        return None

    text = "".join(
        element.itertext()
    ).strip()

    return text or None


# ============================================================
# DISCOVER ALL WMTS LAYERS
# ============================================================

def discover_layers() -> list[dict[str, Any]]:
    xml = get_capabilities_xml()
    root = ET.fromstring(xml)

    layers: list[dict[str, Any]] = []

    for layer in root.iter():

        if _strip_namespace(layer.tag) != "Layer":
            continue

        identifier = None
        title = None
        abstract = None

        formats: list[str] = []
        matrix_sets: list[str] = []
        resource_urls: list[str] = []

        for child in layer:

            name = _strip_namespace(
                child.tag
            )

            if name == "Identifier":
                identifier = _text(child)

            elif name == "Title":
                title = _text(child)

            elif name == "Abstract":
                abstract = _text(child)

            elif name == "Format":

                value = _text(child)

                if value:
                    formats.append(value)

            elif name == "TileMatrixSetLink":

                for nested in child:

                    if (
                        _strip_namespace(
                            nested.tag
                        )
                        == "TileMatrixSet"
                    ):

                        value = _text(
                            nested
                        )

                        if value:
                            matrix_sets.append(
                                value
                            )

            elif name == "ResourceURL":

                template = child.attrib.get(
                    "template"
                )

                if template:
                    resource_urls.append(
                        template
                    )

        if identifier:

            layers.append(
                {
                    "identifier": identifier,
                    "title": title,
                    "abstract": abstract,
                    "formats": formats,
                    "tile_matrix_sets": list(
                        dict.fromkeys(
                            matrix_sets
                        )
                    ),
                    "resource_urls": resource_urls,
                }
            )

    return layers


# ============================================================
# SEARCH
# ============================================================

def find_relevant_layers(
    keyword: str,
    limit: int = 20,
) -> list[dict[str, Any]]:

    keyword = keyword.lower().strip()

    results = []

    for layer in discover_layers():

        identifier = (
            layer.get("identifier", "")
            or ""
        ).lower()

        title = (
            layer.get("title", "")
            or ""
        ).lower()

        abstract = (
            layer.get("abstract", "")
            or ""
        ).lower()

        score = 0

        if keyword in identifier:
            score += 5

        if keyword in title:
            score += 4

        if keyword in abstract:
            score += 2

        if score > 0:

            item = dict(layer)
            item["_score"] = score

            results.append(item)

    results.sort(
        key=lambda item:
        item.get("_score", 0),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# CLASSIFY LAYER
# ============================================================

def classify_layer(
    layer: dict[str, Any],
) -> str:

    text = " ".join(
        [
            str(
                layer.get(
                    "identifier",
                    ""
                )
            ),
            str(
                layer.get(
                    "title",
                    ""
                )
            ),
            str(
                layer.get(
                    "abstract",
                    ""
                )
            ),
        ]
    ).lower()

    if (
        "chlorophyll" in text
        or "/chl" in text
        or "_chl" in text
    ):
        return "chlorophyll"

    if (
        "temperature" in text
        or "sea temperature" in text
        or "/thetao" in text
    ):
        return "sst"

    if (
        "wave" in text
        or "significant wave" in text
        or "/vhm0" in text
        or "/swh" in text
    ):
        return "waves"

    if (
        "current" in text
        or "velocity" in text
        or "/uo" in text
        or "/vo" in text
        or "sea_water_velocity" in text
    ):
        return "currents"

    return "other"


# ============================================================
# ORCA CATEGORIZATION
# ============================================================

def discover_orca_layers(
    layers: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    result = {
        "sst": [],
        "currents": [],
        "waves": [],
        "chlorophyll": [],
        "other": [],
    }

    for layer in layers:

        category = classify_layer(
            layer
        )

        result.setdefault(
            category,
            []
        ).append(layer)

    return result


# ============================================================
# SCORE CANDIDATE
# ============================================================

def _layer_score(
    parameter: str,
    layer: dict[str, Any],
) -> int:

    identifier = (
        layer.get(
            "identifier",
            ""
        )
        or ""
    ).lower()

    title = (
        layer.get(
            "title",
            ""
        )
        or ""
    ).lower()

    abstract = (
        layer.get(
            "abstract",
            ""
        )
        or ""
    ).lower()

    text = (
        identifier
        + " "
        + title
        + " "
        + abstract
    )

    score = 0

    if (
        "analysisforecast" in text
        or "analysis" in text
        or "forecast" in text
    ):
        score += 5

    if (
        "nrt" in text
        or "near real time" in text
    ):
        score += 3

    if "anomaly" in text:
        score -= 8

    if "percentile" in text:
        score -= 8

    if "extreme" in text:
        score -= 6

    if "climatology" in text:
        score -= 5

    if parameter == "sst":

        if "/thetao" in identifier:
            score += 15

        if (
            "sea temperature" in title
            or
            "sea surface temperature" in title
        ):
            score += 10

    elif parameter == "currents":

        if "sea_water_velocity" in identifier:
            score += 15

        if "/uo" in identifier:
            score += 10

        if "/vo" in identifier:
            score += 8

        if "current" in title:
            score += 8

    elif parameter == "waves":

        if "/vhm0" in identifier:
            score += 15

        if "significant wave" in title:
            score += 10

        if "wave height" in title:
            score += 10

    elif parameter == "chlorophyll":

        if "/chl" in identifier:
            score += 15

        if "chlorophyll" in title:
            score += 10

    return score


# ============================================================
# BEST ORCA LAYER
# ============================================================

def get_orca_wmts_layer(
    parameter: str,
) -> dict[str, Any]:

    parameter = parameter.lower().strip()

    supported = {
        "sst",
        "currents",
        "waves",
        "chlorophyll",
    }

    if parameter not in supported:

        raise ValueError(
            f"Unsupported map parameter "
            f"'{parameter}'. "
            f"Supported values: "
            f"{', '.join(sorted(supported))}"
        )

    layers = discover_layers()

    candidates = [
        layer
        for layer in layers
        if classify_layer(layer)
        == parameter
    ]

    if not candidates:

        raise ValueError(
            f"No Copernicus WMTS layer found "
            f"for parameter '{parameter}'."
        )

    candidates.sort(
        key=lambda layer:
        _layer_score(
            parameter,
            layer,
        ),
        reverse=True,
    )

    selected = candidates[0]

    identifier = selected[
        "identifier"
    ]

    title = (
        selected.get("title")
        or parameter.upper()
    )

    if parameter == "currents":
        unit = "m/s"

    elif parameter == "waves":
        unit = "m"

    elif parameter == "chlorophyll":
        unit = "mg/m³"

    else:
        unit = "°C"

    matrix_sets = selected.get(
        "tile_matrix_sets",
        []
    )

    matrix_set = None

    for candidate in matrix_sets:

        normalized = (
            candidate
            .replace(" ", "")
            .lower()
        )

        if normalized in {
            "epsg:3857",
            "googlemapscompatible",
        }:

            matrix_set = candidate
            break

    if matrix_set is None:

        for candidate in matrix_sets:

            if "3857" in candidate:

                matrix_set = candidate
                break

    if matrix_set is None:

        matrix_set = "EPSG:3857"

    # Use a style that is actually advertised if possible.
    # Copernicus frequently uses cmap-based styles.
    style = "cmap:thermal"

    return {
        "parameter": parameter,
        "identifier": identifier,
        "layer": identifier,
        "title": title,
        "unit": unit,
        "style": style,
        "matrix_set": matrix_set,
        "formats": selected.get(
            "formats",
            [],
        ),
        "resource_urls": selected.get(
            "resource_urls",
            [],
        ),
    }


# ============================================================
# LEAFLET WMTS TILE TEMPLATE
# ============================================================

def build_orca_tile_template(
    parameter: str,
) -> str:

    definition = get_orca_wmts_layer(
        parameter
    )

    layer = definition["layer"]
    matrix_set = definition["matrix_set"]
    style = definition["style"]

    # IMPORTANT:
    # {z}, {x}, {y} MUST remain literal.
    # Leaflet replaces them dynamically.
    #
    # Do not use urlencode() on these placeholders.

    layer_encoded = quote(
        str(layer),
        safe="/:._-",
    )

    matrix_encoded = quote(
        str(matrix_set),
        safe="/:._-",
    )

    style_encoded = quote(
        str(style),
        safe="/:._-",
    )

    return (
        WMTS_URL
        + "?SERVICE=WMTS"
        + "&VERSION=1.0.0"
        + "&REQUEST=GetTile"
        + "&FORMAT=image/png"
        + f"&LAYER={layer_encoded}"
        + f"&TILEMATRIXSET={matrix_encoded}"
        + "&TILEMATRIX={z}"
        + "&TILEROW={y}"
        + "&TILECOL={x}"
        + f"&STYLE={style_encoded}"
    )


# ============================================================
# LEGEND
# ============================================================

def build_orca_legend_url(
    parameter: str,
) -> str:

    definition = get_orca_wmts_layer(
        parameter
    )

    layer = quote(
        str(definition["layer"]),
        safe="/:._-",
    )

    style = quote(
        str(definition["style"]),
        safe="/:._-",
    )

    return (
        WMTS_URL
        + "?SERVICE=WMTS"
        + "&VERSION=1.0.0"
        + "&REQUEST=GetLegend"
        + f"&LAYER={layer}"
        + f"&STYLE={style}"
        + "&FORMAT=image/svg+xml"
    )


# ============================================================
# TEST TILE URL
# ============================================================

def build_test_tile_url(
    parameter: str,
    z: int = 5,
    x: int = 8,
    y: int = 13,
) -> str:

    definition = get_orca_wmts_layer(
        parameter
    )

    layer = quote(
        str(definition["layer"]),
        safe="/:._-",
    )

    matrix_set = quote(
        str(definition["matrix_set"]),
        safe="/:._-",
    )

    style = quote(
        str(definition["style"]),
        safe="/:._-",
    )

    return (
        WMTS_URL
        + "?SERVICE=WMTS"
        + "&VERSION=1.0.0"
        + "&REQUEST=GetTile"
        + "&FORMAT=image/png"
        + f"&LAYER={layer}"
        + f"&TILEMATRIXSET={matrix_set}"
        + f"&TILEMATRIX={z}"
        + f"&TILEROW={y}"
        + f"&TILECOL={x}"
        + f"&STYLE={style}"
    )