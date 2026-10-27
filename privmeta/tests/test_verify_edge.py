from datetime import datetime, timedelta

from privmeta.verify import date_not_future, gps_plausible, plausible_ev


def _exif_date(moment):
    return moment.strftime("%Y:%m:%d %H:%M:%S")


def test_past_date_is_accepted():
    past = datetime.now() - timedelta(days=365)
    assert date_not_future(_exif_date(past))


def test_near_future_within_tolerance_is_accepted():
    near_future = datetime.now() + timedelta(hours=12)
    assert date_not_future(_exif_date(near_future))


def test_far_future_beyond_tolerance_is_rejected():
    far_future = datetime.now() + timedelta(hours=20)
    assert not date_not_future(_exif_date(far_future))


def test_malformed_date_is_rejected():
    assert not date_not_future("not-a-date")


def test_iso_format_is_rejected():
    assert not date_not_future("2024-01-01 12:00:00")


def test_plausible_ev_accepts_daylight_scene():
    assert plausible_ev(100, 8.0, 1 / 125)


def test_plausible_ev_rejects_extreme_bright():
    assert not plausible_ev(100, 32.0, 1 / 8000)


def test_plausible_ev_rejects_extreme_dark():
    assert not plausible_ev(100, 1.0, 120.0)


def test_plausible_ev_rejects_zero_iso():
    assert not plausible_ev(0, 8.0, 1 / 125)


def test_plausible_ev_rejects_zero_aperture():
    assert not plausible_ev(100, 0.0, 1 / 125)


def test_plausible_ev_rejects_zero_shutter():
    assert not plausible_ev(100, 8.0, 0.0)


def test_gps_plausible_accepts_boundaries():
    assert gps_plausible(0.0, 0.0)
    assert gps_plausible(90.0, 180.0)
    assert gps_plausible(-90.0, -180.0)


def test_gps_plausible_rejects_out_of_range():
    assert not gps_plausible(90.1, 0.0)
    assert not gps_plausible(-90.1, 0.0)
    assert not gps_plausible(0.0, 180.1)
    assert not gps_plausible(0.0, -180.1)
