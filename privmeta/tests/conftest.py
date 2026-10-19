import piexif
import pytest
from PIL import Image


def _build_exif():
    return {
        "0th": {
            piexif.ImageIFD.Make: b"TestMake",
            piexif.ImageIFD.Model: b"TestModel",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2024:01:01 12:00:00",
            piexif.ExifIFD.ISOSpeedRatings: 100,
            piexif.ExifIFD.FNumber: (28, 10),
            piexif.ExifIFD.ExposureTime: (1, 500),
        },
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((41, 1), (0, 1), (0, 1)),
            piexif.GPSIFD.GPSLongitudeRef: b"E",
            piexif.GPSIFD.GPSLongitude: ((29, 1), (0, 1), (0, 1)),
        },
        "1st": {},
        "thumbnail": None,
    }


@pytest.fixture
def jpeg_with_exif(tmp_path):
    path = tmp_path / "sample.jpg"
    image = Image.new("RGB", (100, 100), color=(200, 50, 50))
    image.save(path, "JPEG", exif=piexif.dump(_build_exif()))
    return str(path)


@pytest.fixture
def jpeg_clean(tmp_path):
    path = tmp_path / "clean.jpg"
    image = Image.new("RGB", (100, 100), color=(50, 50, 200))
    image.save(path, "JPEG")
    return str(path)


@pytest.fixture
def png_file(tmp_path):
    path = tmp_path / "sample.png"
    image = Image.new("RGB", (100, 100), color=(0, 255, 0))
    image.save(path, "PNG")
    return str(path)