import math

from app.modules.dispatch.service import _haversine_km


def test_same_point_is_zero():
    assert _haversine_km(0.0, 0.0, 0.0, 0.0) == 0.0


def test_known_distance_paris_london():
    # ~343 km
    d = _haversine_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert 330 < d < 360


def test_symmetry():
    a = _haversine_km(10.0, 20.0, 30.0, 40.0)
    b = _haversine_km(30.0, 40.0, 10.0, 20.0)
    assert math.isclose(a, b, rel_tol=1e-9)