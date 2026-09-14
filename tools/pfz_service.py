from __future__ import annotations

import math

import httpx


def find_nearest_pfz(
    latitude: float,
    longitude: float,
) -> dict:

    offsets = [

        (0.20, 0.20),
        (0.20, -0.20),
        (-0.20, 0.20),
        (-0.20, -0.20),

        (0.35, 0.00),
        (-0.35, 0.00),
        (0.00, 0.35),
        (0.00, -0.35),
    ]

    candidates = []

    for dlat, dlon in offsets:

        candidate_lat = (
            latitude + dlat
        )

        candidate_lon = (
            longitude + dlon
        )

        try:

            response = httpx.get(

                "https://marine-api.open-meteo.com/v1/marine",

                params={
                    "latitude":
                        candidate_lat,

                    "longitude":
                        candidate_lon,

                    "current":
                        "sea_surface_temperature",
                },

                timeout=15,
            )

            response.raise_for_status()

            data = response.json()

            current = (
                data.get(
                    "current",
                    {},
                )
            )

            sst = current.get(
                "sea_surface_temperature"
            )

            if sst is None:
                continue

            distance = math.hypot(
                dlat * 111,
                dlon * 106,
            )

            score = max(
                0.0,
                1.0
                -
                abs(
                    float(sst) - 28.0
                ) / 4.0,
            )

            candidates.append({

                "latitude":
                    candidate_lat,

                "longitude":
                    candidate_lon,

                "distance_km":
                    round(
                        distance,
                        1,
                    ),

                "sst_c":
                    sst,

                "heuristic_score":
                    round(
                        score,
                        3,
                    ),
            })

        except Exception:
            continue

    candidates.sort(
        key=lambda x: (
            -x["heuristic_score"],
            x["distance_km"],
        )
    )

    return {

        "status":
            "HEURISTIC",

        "source":
            "ORCA prototype PFZ estimator",

        "nearest_candidate":
            (
                candidates[0]
                if candidates
                else None
            ),

        "candidates":
            candidates[:5],

        "important":
            (
                "This is NOT an official PFZ bulletin. "
                "It is a prototype spatial SST heuristic. "
                "Use the approved INCOIS/MOSDAC PFZ product "
                "for operational fishing-zone information."
            ),
    }