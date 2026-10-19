import math
import random

import piexif

from ..errors import PrivMetaError
from . import exif


def has_gps(path):
    data = exif.read(path)
    return bool(data.get("GPS"))


def read(path):
    data = exif.read(path)
    return data.get("GPS") or {}


def strip(source, target):
    data = exif.read(source)
    if not data.get("GPS"):
        raise PrivMetaError("No GPS data found")
    data["GPS"] = {}
    exif.write(source, data, target)


def validate(lat, lon):
    if not -90.0 <= lat <= 90.0:
        raise PrivMetaError(f"Latitude out of range: {lat}")
    if not -180.0 <= lon <= 180.0:
        raise PrivMetaError(f"Longitude out of range: {lon}")


def haversine(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return 2.0 * radius * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def random_point(center_lat, center_lon, radius_km):
    validate(center_lat, center_lon)
    if radius_km <= 0:
        raise PrivMetaError(f"Radius must be positive: {radius_km}")
    distance = random.uniform(0.0, radius_km)
    bearing = random.uniform(0.0, 2.0 * math.pi)
    lat_offset = distance / 111.32
    lon_offset = distance / (111.32 * math.cos(math.radians(center_lat)))
    lat = center_lat + lat_offset * math.cos(bearing)
    lon = center_lon + lon_offset * math.sin(bearing)
    return max(-90.0, min(90.0, lat)), max(-180.0, min(180.0, lon))


def _dms_rational(value):
    absolute = abs(value)
    degrees = int(absolute)
    minutes_float = (absolute - degrees) * 60.0
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60.0
    seconds_rational = (int(round(seconds * 10000)), 10000)
    return ((degrees, 1), (minutes, 1), seconds_rational)


def build(lat, lon, altitude=None, direction=None):
    validate(lat, lon)
    gps = {
        piexif.GPSIFD.GPSLatitudeRef: "N" if lat >= 0 else "S",
        piexif.GPSIFD.GPSLatitude: _dms_rational(lat),
        piexif.GPSIFD.GPSLongitudeRef: "E" if lon >= 0 else "W",
        piexif.GPSIFD.GPSLongitude: _dms_rational(lon),
    }
    if altitude is not None:
        gps[piexif.GPSIFD.GPSAltitudeRef] = 0 if altitude >= 0 else 1
        gps[piexif.GPSIFD.GPSAltitude] = (int(round(abs(altitude) * 100)), 100)
    if direction is not None:
        gps[piexif.GPSIFD.GPSImgDirectionRef] = "T"
        gps[piexif.GPSIFD.GPSImgDirection] = (int(round(direction)) % 360, 1)
    return gps


def attach(source, target, lat, lon, altitude=None, direction=None):
    data = exif.read(source)
    data["GPS"] = build(lat, lon, altitude, direction)
    exif.write(source, data, target)