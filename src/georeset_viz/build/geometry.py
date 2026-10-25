"""Shrink polygon outlines for display."""

import json

import shapely

from georeset_viz import config


def simplified_geojson(wkb: bytes) -> dict:
    shape = shapely.simplify(shapely.from_wkb(wkb), config.SIMPLIFY_DEGREES)
    return json.loads(shapely.to_geojson(shapely.set_precision(shape, 1e-6)))
