import math
from datetime import datetime, timezone


def ev_for(iso, aperture, shutter):
    if iso <= 0 or aperture <= 0 or shutter <= 0:
        return None
    return math.log2((aperture * aperture) / shutter) - math.log2(iso / 100.0)


def plausible_ev(iso, aperture, shutter):
    ev = ev_for(iso, aperture, shutter)
    if ev is None:
        return False
    return -6.0 <= ev <= 18.0


def date_not_future(date_str):
    try:
        parsed = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return parsed <= datetime.now(timezone.utc)


def gps_plausible(lat, lon):
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0