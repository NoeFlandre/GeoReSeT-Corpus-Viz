from georeset_viz.hexes import hex_cell, hex_ring


def test_nearby_points_share_a_cell():
    assert hex_cell(45.7600, 4.8300) == hex_cell(45.7601, 4.8301)
    assert hex_cell(45.76, 4.83) != hex_cell(45.19, 5.72)


def test_hex_ring_is_closed_lon_lat_and_rounded():
    ring = hex_ring(hex_cell(45.19, 5.72))
    assert len(ring) == 7 and ring[0] == ring[-1]
    lon, lat = ring[0]
    assert 5.5 < lon < 5.9 and 45.0 < lat < 45.4
    assert lon == round(lon, 5)
