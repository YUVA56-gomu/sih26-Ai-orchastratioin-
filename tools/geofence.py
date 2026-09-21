from __future__ import annotations

from typing import Any, Dict
from tools.gis_service import get_gis_service


def check_geofence(
    latitude: float,
    longitude: float,
) -> Dict[str, Any]:
    """
    Check geospatial boundaries, EEZ, MPAs, and restricted zones for a location.

    Uses the deterministic SAMUDRA GIS Spatial Engine (tools/gis_service.py).
    """
    service = get_gis_service()
    return service.check_geofence(latitude, longitude)