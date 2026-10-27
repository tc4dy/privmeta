import json
import math
import os
import random
from datetime import datetime, timezone

import piexif

from ..errors import PrivMetaError, UnsupportedFormat
from ..fsio import collect, resolve_output
from ..image import exif, gps, thumb
from ..output import fail, info, ok, warn
from ..sniff import detect, IMAGE
from .. import timeline

_PROFILE_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles"
)


def _source_mode(path):
    try:
        return os.stat(path).st_mode & 0o777
    except OSError:
        return None


def _load_json(name):
    path = os.path.join(_PROFILE_ROOT, name)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivMetaError(f"Cannot load profile {name}: {exc}")


def _select_camera(cameras, name):
    if name:
        entry = cameras.get(name)
        if entry is None:
            available = ", ".join(sorted(cameras.keys()))
            raise PrivMetaError(f"Unknown camera: {name} (available: {available})")
        return name, entry
    key = random.choice(sorted(cameras.keys()))
    return key, cameras[key]


def _select_lens(lenses, camera_key):
    options = lenses.get(camera_key)
    if not options:
        return None
    return random.choice(options)


def _select_city(cities, name):
    if not name:
        return None, None
    entry = cities.get(name)
    if entry is None:
        available = ", ".join(sorted(cities.keys()))
        raise PrivMetaError(f"Unknown city: {name} (available: {available})")
    return name, entry


def _rational(value, scale=10):
    return (int(round(value * scale)), scale)


def _shutter(value):
    if value >= 1:
        return (int(round(value)), 1)
    return (1, int(round(1.0 / value)))


def _pick_iso(camera):
    return random.choice(camera["isos"])


def _pick_aperture(camera):
    return random.choice(camera["apertures"])


def _pick_shutter(camera):
    return random.choice(camera["shutters"])


def _pick_focal(camera, lens):
    if lens:
        return random.randint(lens["focal_min"], lens["focal_max"])
    return random.randint(camera["focal_min"], camera["focal_max"])


def _build_exif(camera, date_value, lens, city, radius, thumbnail_bytes):
    iso = _pick_iso(camera)
    aperture = _pick_aperture(camera)
    shutter = _pick_shutter(camera)
    focal = _pick_focal(camera, lens)
    data = {
        "0th": {
            piexif.ImageIFD.Make: camera["make"],
            piexif.ImageIFD.Model: camera["model"],
            piexif.ImageIFD.Software: camera["software"],
            piexif.ImageIFD.Orientation: 1,
        },
        "Exif": {
            piexif.ExifIFD.ISOSpeedRatings: iso,
            piexif.ExifIFD.FNumber: _rational(aperture),
            piexif.ExifIFD.ExposureTime: _shutter(shutter),
            piexif.ExifIFD.FocalLength: (focal, 1),
            piexif.ExifIFD.DateTimeOriginal: date_value.strftime("%Y:%m:%d %H:%M:%S"),
            piexif.ExifIFD.DateTimeDigitized: date_value.strftime("%Y:%m:%d %H:%M:%S"),
        },
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }
    if lens:
        data["Exif"][piexif.ExifIFD.LensModel] = lens["name"]
        apex = int(round(2.0 * math.log2(lens["aperture_max"])))
        data["Exif"][piexif.ExifIFD.MaxApertureValue] = (apex, 1)
    if city:
        lat, lon = gps.random_point(city["lat"], city["lon"], radius or city["radius_km"])
        data["GPS"] = gps.build(
            lat,
            lon,
            altitude=city["alt"] + random.uniform(-15.0, 15.0),
            direction=random.randint(0, 359),
        )
    if thumbnail_bytes:
        data["thumbnail"] = thumbnail_bytes
        data["1st"] = {
            piexif.ImageIFD.Compression: 6,
            piexif.ImageIFD.XResolution: (72, 1),
            piexif.ImageIFD.YResolution: (72, 1),
            piexif.ImageIFD.Orientation: 1,
        }
    return data


def _merge(existing, incoming):
    for section in ("0th", "Exif", "GPS"):
        existing.setdefault(section, {})
        for key, value in incoming.get(section, {}).items():
            existing[section][key] = value
    if incoming.get("thumbnail"):
        existing["thumbnail"] = incoming["thumbnail"]
        existing["1st"] = incoming.get("1st", {})
    return existing


def _parse_range(value):
    parts = value.split(":")
    if len(parts) != 2:
        raise PrivMetaError("--date-range must be START:END")
    try:
        start = datetime.fromisoformat(parts[0])
        end = datetime.fromisoformat(parts[1])
    except ValueError as exc:
        raise PrivMetaError(f"Invalid date in --date-range: {exc}")
    if end < start:
        raise PrivMetaError("--date-range end must not be before start")
    return start, end


def _pick_date(args, index, total):
    if not args.date_range:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    start, end = _parse_range(args.date_range)
    if args.timeline:
        schedule = timeline.sequential(start, end, total)
        return schedule[index - 1]
    return timeline.random_between(start, end)


def _handle_one(source, args, cameras, lenses, cities, index, total, counters):
    try:
        family, label = detect(source)
        if family != IMAGE:
            warn(f"skipped (not an image): {source}")
            counters["skipped"] += 1
            return
        camera_key, camera = _select_camera(cameras, args.camera)
        _, city = _select_city(cities, args.city)
        lens = _select_lens(lenses, camera_key)
        chosen = _pick_date(args, index, total)
        payload = thumb.create(source) if args.thumbnail else None
        incoming = _build_exif(camera, chosen, lens, city, args.radius, payload)
        target = resolve_output(source, args.output_dir, suffix="_faked")
        mode = _source_mode(source) if args.inplace else None
        if args.preserve:
            final = _merge(exif.read(source), incoming)
        else:
            final = incoming
        exif.write(source, final, target)
        if args.inplace:
            os.replace(target, source)
            if mode is not None:
                try:
                    os.chmod(source, mode)
                except OSError:
                    pass
            target = source
        ok(f"faked: {source} -> {target}")
        counters["ok"] += 1
    except (PrivMetaError, UnsupportedFormat, OSError) as exc:
        fail(f"{source}: {exc}")
        counters["fail"] += 1
        if args.fail_fast:
            raise


def run(args):
    if args.seed is not None:
        random.seed(args.seed)
    cameras = _load_json("cameras.json")
    lenses = _load_json("lenses.json")
    cities = _load_json("cities.json")
    targets, warnings = collect(args.paths, args.recursive)
    for message in warnings:
        warn(message)
    if args.city and args.city not in cities:
        fail(f"unknown city: {args.city}")
        return 2
    if args.camera and args.camera not in cameras:
        fail(f"unknown camera: {args.camera}")
        return 2
    info(f"targets: {len(targets)}")
    counters = {"ok": 0, "fail": 0, "skipped": 0}
    for index, source in enumerate(targets, start=1):
        try:
            _handle_one(source, args, cameras, lenses, cities, index, len(targets), counters)
        except PrivMetaError as exc:
            fail(str(exc))
            return 2
    ok(f"done: {counters['ok']} ok, {counters['fail']} failed, {counters['skipped']} skipped")
    return 0 if counters["fail"] == 0 else 2
