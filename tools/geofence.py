from __future__ import annotations

from math import (
    atan2,
    cos,
    radians,
    sin,
    sqrt,
)


DEMO_ZONES = [
    {
        "name": "Demo Marine Protected Zone",
        "latitude": 17.78,
        "longitude": 83.38,
        "radius_km": 8.0,
        "type": "MPA_DEMO",
    }
]


def _distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    earth_radius = 6371.0

    p1 = radians(lat1)
    p2 = radians(lat2)

    dlat = radians(
        lat2 - lat1
    )

    dlon = radians(
        lon2 - lon1
    )

    a = (
        sin(dlat / 2) ** 2
        +
        cos(p1)
        *
        cos(p2)
        *
        sin(dlon / 2) ** 2
    )

    return (
        2
        *
        earth_radius
        *
        atan2(
            sqrt(a),
            sqrt(1 - a),
        )
    )


def check_geofence(
    latitude: float,
    longitude: float,
) -> dict:

    matches = []

    for zone in DEMO_ZONES:

        distance = _distance_km(
            latitude,
            longitude,
            zone["latitude"],
            zone["longitude"],
        )

        if distance <= zone["radius_km"]:

            matches.append({
                "name":
                    zone["name"],

                "type":
                    zone["type"],

                "distance_km":
                    round(
                        distance,
                        2,
                    ),
            })

    return {

        "status":
            "OK",

        "inside_restricted_zone":
            bool(matches),

        "matches":
            matches,

        "source":
            "ORCA geofence layer",

        "data_quality":
            "DEMO",

        "warning":
            (
                "This is demonstration geometry. "
                "Authoritative MPA, EEZ and restricted-zone "
                "datasets must be connected before operational use."
            ),
    }