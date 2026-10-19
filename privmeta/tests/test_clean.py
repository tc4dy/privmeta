import piexif
import pytest

from privmeta.commands import clean as clean_cmd
from privmeta.errors import PrivMetaError


def _args(paths, **overrides):
    ns = type("Args", (), {})()
    ns.paths = paths
    ns.all_fields = overrides.get("all_fields", True)
    ns.drop = overrides.get("drop")
    ns.keep = overrides.get("keep")
    ns.recursive = overrides.get("recursive", False)
    ns.output_dir = overrides.get("output_dir")
    ns.inplace = overrides.get("inplace", False)
    ns.keep_backup = overrides.get("keep_backup", False)
    ns.rename = overrides.get("rename", False)
    ns.reset_time = overrides.get("reset_time", False)
    ns.dry_run = overrides.get("dry_run", False)
    ns.fail_fast = overrides.get("fail_fast", False)
    return ns


def test_clean_all_removes_exif(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output))
    code = clean_cmd.run(ns)
    assert code == 0
    target = output / "sample_cleaned.jpg"
    assert target.exists()
    data = piexif.load(str(target))
    assert not data.get("0th")
    assert not data.get("Exif")
    assert not data.get("GPS")


def test_clean_drop_gps_only(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], all_fields=False, drop="gps", output_dir=str(output))
    code = clean_cmd.run(ns)
    assert code == 0
    target = output / "sample_cleaned.jpg"
    data = piexif.load(str(target))
    assert not data.get("GPS")
    assert data.get("0th")


def test_clean_keep_exif(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], all_fields=False, keep="exif", output_dir=str(output))
    code = clean_cmd.run(ns)
    assert code == 0
    target = output / "sample_cleaned.jpg"
    data = piexif.load(str(target))
    assert data.get("0th")
    assert not data.get("GPS")


def test_clean_drop_and_keep_conflict(jpeg_with_exif):
    ns = _args([jpeg_with_exif], all_fields=False, drop="gps", keep="exif")
    with pytest.raises(PrivMetaError):
        clean_cmd.run(ns)


def test_clean_dry_run(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output), dry_run=True)
    code = clean_cmd.run(ns)
    assert code == 0
    assert not (output / "sample_cleaned.jpg").exists()