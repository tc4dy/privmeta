import pytest

from privmeta.errors import UnsupportedFormat
from privmeta.sniff import detect, IMAGE


def test_detect_jpeg(jpeg_with_exif):
    family, label = detect(jpeg_with_exif)
    assert family == IMAGE
    assert label == "jpeg"


def test_detect_png(png_file):
    family, label = detect(png_file)
    assert family == IMAGE
    assert label == "png"


def test_detect_rejects_unknown(tmp_path):
    path = tmp_path / "unknown.bin"
    path.write_bytes(b"\x00\x01\x02\x03" * 10)
    with pytest.raises(UnsupportedFormat):
        detect(str(path))