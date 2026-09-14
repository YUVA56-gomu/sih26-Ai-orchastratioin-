from tools.copernicus_wmts import (
    discover_layers,
    discover_orca_layers,
)


def main() -> None:

    print("=" * 80)
    print("ORCA — COPERNICUS WMTS DISCOVERY")
    print("=" * 80)
    print()

    print(
        "Downloading live Copernicus WMTS catalogue..."
    )

    layers = discover_layers()

    print(
        f"Total advertised layers: {len(layers)}"
    )

    print()

    categorized = discover_orca_layers(
        layers
    )

    for category, items in categorized.items():

        print("=" * 80)
        print(
            f"{category.upper()} "
            f"({len(items)} layers)"
        )
        print("=" * 80)

        for layer in items[:10]:

            print(
                "IDENTIFIER:",
                layer["identifier"],
            )

            print(
                "TITLE:",
                layer["title"],
            )

            print(
                "MATRIX SETS:",
                layer["tile_matrix_sets"],
            )

            print(
                "DIMENSIONS:",
                layer["dimensions"],
            )

            print()


if __name__ == "__main__":
    main()