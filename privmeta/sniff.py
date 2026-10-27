from .errors import UnsupportedFormat

IMAGE = "image"
PDF = "pdf"
OFFICE = "office"
AUDIO = "audio"
VIDEO = "video"

_ISO_BMFF_IMAGE = frozenset({
    b"heic", b"heix", b"hevc", b"heim", b"heis", b"heif", b"heifs",
    b"mif1", b"msf1", b"avif", b"avis",
})
_ISO_BMFF_VIDEO = frozenset({
    b"isom", b"iso2", b"iso4", b"iso5", b"iso6",
    b"mp41", b"mp42", b"mp71", b"avc1", b"dash",
    b"M4V ", b"m4v ", b"qt  ",
    b"3gp4", b"3gp5", b"3gp6", b"3g2a",
    b"F4V ", b"f4v ",
})
_ISO_BMFF_AUDIO = frozenset({
    b"M4A ", b"M4B ", b"M4P ", b"m4a ", b"m4b ", b"m4p ",
    b"F4A ", b"F4B ", b"f4a ", b"f4b ",
})

_SIGNATURES = (
    (b"\xff\xd8\xff", IMAGE, "jpeg"),
    (b"\x89PNG\r\n\x1a\n", IMAGE, "png"),
    (b"%PDF", PDF, "pdf"),
    (b"PK\x03\x04", OFFICE, "zip"),
    (b"ID3", AUDIO, "mp3"),
    (b"fLaC", AUDIO, "flac"),
)


def _read_head(path, size=32):
    with open(path, "rb") as handle:
        return handle.read(size)


def _classify_iso_bmff(brand, path):
    if brand in _ISO_BMFF_IMAGE:
        if brand in (b"avif", b"avis"):
            return IMAGE, "avif"
        return IMAGE, "heic"
    if brand in _ISO_BMFF_VIDEO:
        return VIDEO, "mp4"
    if brand in _ISO_BMFF_AUDIO:
        return AUDIO, "m4a"
    raise UnsupportedFormat(f"Unknown ISO BMFF brand {brand!r} in {path}")


def detect(path):
    head = _read_head(path, 32)
    if len(head) >= 12 and head[4:8] == b"ftyp":
        return _classify_iso_bmff(head[8:12], path)
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return IMAGE, "webp"
    for signature, family, label in _SIGNATURES:
        if head.startswith(signature):
            return family, label
    raise UnsupportedFormat(f"Unrecognised file signature in {path}")


def family_of(path):
    return detect(path)[0]
