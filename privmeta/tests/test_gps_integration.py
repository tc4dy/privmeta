import piexif

from privmeta.image import gps


def _decode_dms(value):
    degrees, minutes, seconds = value
    return (
        degrees[0] / degrees[1]
        + (minutes[0] / minutes[1]) / 60.0
        + (seconds[0] / seconds[1]) / 3600.0
    )


def _wrap(gps_data):
    return {
        "0th": {},
        "Exif": {},
        "GPS": gps_data,
        "1st": {},
        "thumbnail": None,
    }


def test_build_output_passes_piexif_dump():
    payload = _wrap(gps.build(41.0082, 28.9784, altitude=40.0, direction=180))
    serialized = piexif.dump(payload)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0


def test_build_roundtrip_preserves_coordinate():
    payload = _wrap(gps.build(41.0082, 28.9784))
    roundtripped = piexif.load(piexif.dump(payload))
    decoded_lat = _decode_dms(roundtripped["GPS"][piexif.GPSIFD.GPSLatitude])
    decoded_lon = _decode_dms(roundtripped["GPS"][piexif.GPSIFD.GPSLongitude])
    assert abs(decoded_lat - 41.0082) < 0.0001
    assert abs(decoded_lon - 28.9784) < 0.0001


def test_build_southern_hemisphere_roundtrip():
    payload = _wrap(gps.build(-33.8688, -70.6693))
    roundtripped = piexif.load(piexif.dump(payload))
    assert roundtripped["GPS"][piexif.GPSIFD.GPSLatitudeRef] == b"S"
    assert roundtripped["GPS"][piexif.GPSIFD.GPSLongitudeRef] == b"W"
    decoded_lat = _decode_dms(roundtripped["GPS"][piexif.GPSIFD.GPSLatitude])
    decoded_lon = _decode_dms(roundtripped["GPS"][piexif.GPSIFD.GPSLongitude])
    assert abs(decoded_lat - 33.8688) < 0.0001
    assert abs(decoded_lon - 70.6693) < 0.0001


def test_build_near_minute_rollover_roundtrips():
    payload = _wrap(gps.build(41.99999999, 28.9784))
    roundtripped = piexif.load(piexif.dump(payload))
    decoded_lat = _decode_dms(roundtripped["GPS"][piexif.GPSIFD.GPSLatitude])
    assert abs(decoded_lat - 42.0) < 0.0001
    assert roundtripped["GPS"][piexif.GPSIFD.GPSLatitudeRef] == b"N"


def test_build_with_altitude_and_direction_roundtrips():
    payload = _wrap(gps.build(41.0082, 28.9784, altitude=-12.5, direction=270))
    roundtripped = piexif.load(piexif.dump(payload))
    assert piexif.GPSIFD.GPSAltitude in roundtripped["GPS"]
    assert piexif.GPSIFD.GPSImgDirection in roundtripped["GPS"]
    altitude_ref = roundtripped["GPS"][piexif.GPSIFD.GPSAltitudeRef]
    assert altitude_ref == 1
