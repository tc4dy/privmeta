from .errors import UnsupportedFormat

IMAGE = "image"
PDF = "pdf"
OFFICE = "office"
AUDIO = "audio"
VIDEO = "video"

_SIGNATURES = (
    (b"\xff\xd8\xff", IMAGE, "jpeg"),
    (b"\x89PNG\r\n\x1a\n", IMAGE, "png"),
    (b"RIFF", IMAGE, "webp"),
    (b"%PDF", PDF, "pdf"),
    (b"PK\x03\x04", OFFICE, "zip"),
    (b"ID3", AUDIO, "mp3"),
    (b"fLaC", AUDIO, "flac"),
)


def _read_head(path, size=32):
    with open(path, "rb") as handle:
        return handle.read(size)


def detect(path):
    head = _read_head(path, 32)
    if head[4:8] == b"ftyp":
        return VIDEO, "mp4"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return IMAGE, "webp"
    for signature, family, label in _SIGNATURES:
        if head.startswith(signature):
            if label == "webp":
                continue
            return family, label
    raise UnsupportedFormat(f"Unrecognised file signature in {path}")


def family_of(path):
    return detect(path)[0]