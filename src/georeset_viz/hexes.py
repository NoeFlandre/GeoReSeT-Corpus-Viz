"""H3 hexagons that the map uses to count places."""

import h3

from georeset_viz import config


def hex_cell(lat: float, lon: float) -> str:
    return h3.latlng_to_cell(lat, lon, config.HEX_RESOLUTION)


def hex_ring(cell: str) -> list[list[float]]:
    ring = [[round(lon, 5), round(lat, 5)] for lat, lon in h3.cell_to_boundary(cell)]
    return [*ring, ring[0]]
