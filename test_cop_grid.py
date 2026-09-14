from __future__ import annotations

from pprint import pprint

from dotenv import load_dotenv

from tools.copernicus_grid import (
    get_copernicus_grid,
)


load_dotenv()


def main() -> None:

    print("=" * 70)
    print("ORCA — COPERNICUS SST GRID TEST")
    print("=" * 70)

    result = get_copernicus_grid(

        "sst",

        minimum_latitude=16.5,
        maximum_latitude=18.5,

        minimum_longitude=82.0,
        maximum_longitude=84.0,
    )


    print()

    print(
        "Parameter:",
        result["parameter"],
    )

    print(
        "Observation:",
        result["observation_time"],
    )

    print(
        "Dataset:",
        result["dataset_id"],
    )

    print(
        "Grid shape:",
        result["shape"],
    )

    print(
        "Latitude points:",
        len(result["latitudes"]),
    )

    print(
        "Longitude points:",
        len(result["longitudes"]),
    )

    print()

    pprint(
        result,
        sort_dicts=False,
    )


if __name__ == "__main__":
    main()