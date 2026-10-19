import shutil

import piexif
from PIL import Image

from ..errors import PrivMetaError, UnsupportedFormat
from ..sniff import detect, IMAGE


def _wrap_piexif_error(exc, path):
    return PrivMetaError(f"EXIF operation failed on {path}: {exc}")


def read(path):
    try:
        return piexif.load(path)
    except (piexif.InvalidImageDataError, ValueError, TypeError) as exc:
        raise _wrap_piexif_error(exc, path)


def has_exif(path):
    try:
        data = piexif.load(path)
    except (piexif.InvalidImageDataError, ValueError, TypeError):
        return False
    for section in ("0th", "Exif", "GPS", "1st"):
        if data.get(section):
            return True
    return False


def dump(data):
    try:
        return piexif.dump(data)
    except (ValueError, TypeError, piexif.InvalidImageDataError) as exc:
        raise PrivMetaError(f"Cannot serialize EXIF: {exc}")


def write(source, data, target):
    family, label = detect(source)
    if family != IMAGE:
        raise UnsupportedFormat(f"EXIF write is not supported for {label}")
    exif_bytes = dump(data)
    if label == "jpeg":
        shutil.copy2(source, target)
        try:
            piexif.insert(exif_bytes, target)
        except (piexif.InvalidImageDataError, ValueError, TypeError) as exc:
            raise _wrap_piexif_error(exc, target)
        return
    try:
        with Image.open(source) as image:
            image.save(target, format=image.format, exif=exif_bytes)
    except OSError as exc:
        raise PrivMetaError(f"Cannot write image {target}: {exc}")


def strip_all(source, target):
    family, label = detect(source)
    if family != IMAGE:
        raise UnsupportedFormat(f"EXIF strip is not supported for {label}")
    if label == "jpeg":
        shutil.copy2(source, target)
        try:
            piexif.remove(target)
        except (piexif.InvalidImageDataError, ValueError, TypeError) as exc:
            raise _wrap_piexif_error(exc, target)
        return
    try:
        with Image.open(source) as image:
            image.save(target, format=image.format)
    except OSError as exc:
        raise PrivMetaError(f"Cannot strip EXIF from {target}: {exc}")


def clear_section(source, target, section):
    data = read(source)
    if section not in data:
        raise PrivMetaError(f"Unknown EXIF section: {section}")
    data[section] = {}
    if section == "1st":
        data["thumbnail"] = None
    write(source, data, target)


def delete_tags(source, target, section, tags):
    data = read(source)
    bucket = data.get(section)
    if bucket is None:
        raise PrivMetaError(f"Unknown EXIF section: {section}")
    for tag in tags:
        bucket.pop(tag, None)
    write(source, data, target)


def thumbnail_present(path):
    data = read(path)
    return bool(data.get("thumbnail"))


def drop_thumbnail(source, target):
    data = read(source)
    if not data.get("thumbnail") and not data.get("1st"):
        raise PrivMetaError("No embedded thumbnail found")
    data["thumbnail"] = None
    data["1st"] = {}
    write(source, data, target)


def attach_thumbnail(source, target, thumbnail_bytes, width, height):
    data = read(source)
    data["thumbnail"] = thumbnail_bytes
    data["1st"] = {
        piexif.ImageIFD.Compression: 6,
        piexif.ImageIFD.XResolution: (72, 1),
        piexif.ImageIFD.YResolution: (72, 1),
        piexif.ImageIFD.Orientation: 1,
    }
    write(source, data, target)


def keep_only(source, target, sections):
    data = read(source)
    for section in ("0th", "Exif", "GPS", "1st"):
        if section not in sections:
            data[section] = {}
    if "1st" not in sections:
        data["thumbnail"] = None
    write(source, data, target)