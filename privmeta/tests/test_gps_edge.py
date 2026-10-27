import pytest

from privmeta.image import gps


def _tick_seconds(seconds_rational):
    numerator, denominator = seconds_rational
    return numerator / denominator


def _tick_rational(value):
    numerator, denominator = value
    return numerator / denominator


def test_dms_never_emits_sixty_seconds():
    for value in (41.0, 41.5, 41.99999, 41.999999, 41.9999999, 59.99999999):
        _deg, _min, sec = gps._dms_rational(value)
        assert _tick_seconds(sec) < 60.0


def test_dms_propagates_minute_carry():
    deg, minute, sec = gps._dms_rational(41.99999999)
    assert _tick_rational(deg) == 42.0
    assert _tick_rational(minute) == 0.0
    assert _tick_seconds(sec) == 0.0


def test_dms_propagates_degree_carry():
    deg, minute, sec = gps._dms_rational(59.99999999)
    assert _tick_rational(deg) == 60.0
    assert _tick_rational(minute) == 0.0
    assert _tick_seconds(sec) == 0.0


def test_dms_uses_absolute_magnitude():
    deg, _min, _sec = gps._dms_rational(-41.5)
    assert _tick_rational(deg) == 41.0


def test_build_sets_north_east_refs():
    data = gps.build(90.0, 180.0)
    assert data[1] == "N"
    assert data[3] == "E"


def test_build_sets_south_west_refs():
    data = gps.build(-33.8688, -70.6693)
    assert data[1] == "S"
    assert data[3] == "W"


def test_random_point_near_pole_returns_in_bounds():
    lat, lon = gps.random_point(89.9999, 0.0, 5.0)
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0


def test_random_point_at_exact_pole_returns_in_bounds():
    lat, lon = gps.random_point(90.0, 0.0, 1.0)
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0


def test_random_point_rejects_zero_radius():
    with pytest.raises(Exception):
        gps.random_point(41.0, 29.0, 0.0)


def test_random_point_rejects_negative_radius():
    with pytest.raises(Exception):
        gps.random_point(41.0, 29.0, -1.0)


def test_haversine_matches_known_distance():
    distance = gps.haversine(41.0082, 28.9784, 39.9334, 32.8597)
    assert 340.0 < distance < 360.0
