import pytest

from privmeta.errors import UnsupportedFormat
from privmeta.sniff import AUDIO, IMAGE, VIDEO, detect


def _bmff_file(tmp_path, name, brand):
    path = tmp_path / name
    header = b"\x00\x00\x00\x20ftyp" + brand + b"\x00\x00\x00\x00" + b"\x00" * 16
    path.write_bytes(header)
    return str(path)


def test_detect_avif(tmp_path):
    path = _bmff_file(tmp_path, "image.avif", b"avif")
    family, label = detect(path)
    assert family == IMAGE
    assert label == "avif"


def test_detect_avis_sequence(tmp_path):
    path = _bmff_file(tmp_path, "seq.avis", b"avis")
    family, label = detect(path)
    assert family == IMAGE
    assert label == "avif"


def test_detect_heif_variant(tmp_path):
    path = _bmff_file(tmp_path, "image.heif", b"heif")
    family, label = detect(path)
    assert family == IMAGE
    assert label == "heic"


def test_detect_heic(tmp_path):
    path = _bmff_file(tmp_path, "image.heic", b"heic")
    family, label = detect(path)
    assert family == IMAGE
    assert label == "heic"


def test_detect_mp4_video(tmp_path):
    path = _bmff_file(tmp_path, "clip.mp4", b"isom")
    family, label = detect(path)
    assert family == VIDEO
    assert label == "mp4"


def test_detect_m4a_audio(tmp_path):
    path = _bmff_file(tmp_path, "track.m4a", b"M4A ")
    family, label = detect(path)
    assert family == AUDIO
    assert label == "m4a"


def test_detect_rejects_unknown_brand(tmp_path):
    path = _bmff_file(tmp_path, "mystery.bin", b"ZZZZ")
    with pytest.raises(UnsupportedFormat):
        detect(path)


def test_detect_webp_ripple(tmp_path):
    path = tmp_path / "image.webp"
    path.write_bytes(b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"VP8 ")
    family, label = detect(str(path))
    assert family == IMAGE
    assert label == "webp"
