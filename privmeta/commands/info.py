import piexif
from ..errors import PrivMetaError, UnsupportedFormat
from ..fsio import collect
from ..media import audio, office, pdf, video
from ..output import fail, info, ok, warn
from ..sniff import detect, IMAGE, PDF, OFFICE, AUDIO, VIDEO
from ..image import exif, xmp

_MEDIA = {
    PDF: pdf,
    OFFICE: office,
    AUDIO: audio,
    VIDEO: video,
}


def _image_info(path):
    lines = []
    family, label = detect(path)
    data = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    if label in ("png", "webp"):
        exif_bytes = xmp.get_exif_bytes(path)
        if exif_bytes:
            try:
                data = piexif.load(exif_bytes)
            except Exception:
                pass
    else:
        try:
            data = exif.read(path)
        except PrivMetaError:
            pass

    for section in ("0th", "Exif", "GPS", "1st"):
        bucket = data.get(section, {})
        if bucket:
            lines.append(f"{section}: {len(bucket)} tags")
    if data.get("thumbnail"):
        lines.append("thumbnail: present")
    try:
        segments = xmp.inspect(path)
        if segments:
            lines.append(f"segments: {', '.join(sorted(set(segments)))}")
    except (PrivMetaError, UnsupportedFormat):
        pass
    return lines


def _handle_one(source, counters):
    try:
        family, label = detect(source)
        if family == IMAGE:
            lines = _image_info(source)
        elif family in _MEDIA:
            data = _MEDIA[family].read(source)
            lines = [f"{key}: {value}" for key, value in data.items()]
        else:
            raise UnsupportedFormat(f"Unsupported format: {label}")
        ok(f"{source} [{label}]")
        for line in lines:
            info(f"  {line}")
        counters["ok"] += 1
    except (PrivMetaError, UnsupportedFormat, OSError) as exc:
        fail(f"{source}: {exc}")
        counters["fail"] += 1


def run(args):
    targets, warnings = collect(args.paths, args.recursive)
    for message in warnings:
        warn(message)
    counters = {"ok": 0, "fail": 0}
    for source in targets:
        _handle_one(source, counters)
    ok(f"done: {counters['ok']} ok, {counters['fail']} failed")
    return 0 if counters["fail"] == 0 else 2
