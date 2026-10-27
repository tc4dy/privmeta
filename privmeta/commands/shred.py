import os

from PIL import Image

from ..errors import PrivMetaError, UnsupportedFormat
from ..fsio import collect, resolve_output
from ..image import exif
from ..media import audio, office, pdf, video
from ..output import fail, info, ok, warn
from ..sniff import detect, IMAGE, PDF, OFFICE, AUDIO, VIDEO
from ..verify import date_not_future, gps_plausible, plausible_ev
from . import clean

_MEDIA = {
    PDF: pdf,
    OFFICE: office,
    AUDIO: audio,
    VIDEO: video,
}


def _source_mode(path):
    try:
        return os.stat(path).st_mode & 0o777
    except OSError:
        return None


def _recompress(source, target, quality):
    try:
        with Image.open(source) as image:
            image.save(target, format=image.format, quality=quality, optimize=True)
    except OSError as exc:
        raise PrivMetaError(f"Recompression failed: {exc}")


def _check(source):
    try:
        data = exif.read(source)
    except PrivMetaError:
        return []
    issues = []
    exif_ifd = data.get("Exif", {})
    gps_ifd = data.get("GPS", {})
    iso = exif_ifd.get(0x8827)
    aperture = exif_ifd.get(0x829D)
    shutter = exif_ifd.get(0x829A)
    if iso and aperture and shutter:
        try:
            f = aperture[0] / aperture[1]
            s = shutter[0] / shutter[1] if shutter[1] else 0.0
            if s > 0 and not plausible_ev(iso, f, s):
                issues.append(f"implausible exposure triangle (ISO {iso})")
        except (IndexError, ZeroDivisionError, TypeError):
            issues.append("malformed exposure fields")
    date_str = exif_ifd.get(0x9003)
    if isinstance(date_str, bytes):
        date_str = date_str.decode("ascii", errors="replace")
    if date_str and not date_not_future(date_str):
        issues.append("DateTimeOriginal is malformed or in the future")
    if gps_ifd:
        try:
            lat = gps_ifd.get(2)
            lon = gps_ifd.get(4)
            if lat and lon:
                lat_val = lat[0][0] / lat[0][1] if lat[0][1] else 0.0
                lon_val = lon[0][0] / lon[0][1] if lon[0][1] else 0.0
                if not gps_plausible(lat_val, lon_val):
                    issues.append("GPS coordinates out of range")
        except (IndexError, ZeroDivisionError, TypeError):
            issues.append("malformed GPS fields")
    return issues


def _strip_image(source, target, passes, label):
    plan = {field: True for field in clean.FIELDS}
    if passes <= 1:
        clean._clean_image(source, target, plan, label)
        return
    previous = source
    pass_files = []
    try:
        for pass_num in range(passes):
            is_final = pass_num == passes - 1
            current_target = target if is_final else f"{target}.pass{pass_num}"
            if not is_final:
                pass_files.append(current_target)
            clean._clean_image(previous, current_target, plan, label)
            if previous != source and os.path.exists(previous):
                try:
                    os.unlink(previous)
                except OSError:
                    pass
            previous = current_target
    except Exception:
        for path in pass_files:
            if os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
        raise
    if previous != target:
        os.replace(previous, target)


def _handle_one(source, args, counters):
    try:
        family, label = detect(source)
        target = resolve_output(source, args.output_dir, suffix="_shred")
        mode = _source_mode(source) if args.inplace else None
        if family == IMAGE:
            _strip_image(source, target, args.passes, label)
            if args.quality:
                temp = target + ".recompressed"
                try:
                    _recompress(target, temp, args.quality)
                    os.replace(temp, target)
                except Exception:
                    if os.path.exists(temp):
                        os.unlink(temp)
                    raise
            if args.check:
                for issue in _check(target):
                    warn(f"{source}: {issue}")
        elif family in _MEDIA:
            _MEDIA[family].strip(source, target)
        else:
            raise UnsupportedFormat(f"Unsupported format: {label}")
        if args.inplace:
            os.replace(target, source)
            if mode is not None:
                try:
                    os.chmod(source, mode)
                except OSError:
                    pass
            target = source
        ok(f"shredded: {source} -> {target}")
        counters["ok"] += 1
    except (PrivMetaError, UnsupportedFormat, OSError) as exc:
        fail(f"{source}: {exc}")
        counters["fail"] += 1
        if args.fail_fast:
            raise


def run(args):
    targets, warnings = collect(args.paths, args.recursive)
    for message in warnings:
        warn(message)
    info(f"targets: {len(targets)}")
    counters = {"ok": 0, "fail": 0}
    for source in targets:
        try:
            _handle_one(source, args, counters)
        except PrivMetaError as exc:
            fail(str(exc))
            return 2
    ok(f"done: {counters['ok']} ok, {counters['fail']} failed")
    return 0 if counters["fail"] == 0 else 2
