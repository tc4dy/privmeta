import piexif

from privmeta.commands import shred as shred_cmd


def _args(paths, **overrides):
    ns = type("Args", (), {})()
    ns.paths = paths
    ns.passes = overrides.get("passes", 1)
    ns.quality = overrides.get("quality")
    ns.check = overrides.get("check", False)
    ns.recursive = overrides.get("recursive", False)
    ns.output_dir = overrides.get("output_dir")
    ns.inplace = overrides.get("inplace", False)
    ns.fail_fast = overrides.get("fail_fast", False)
    return ns


def test_shred_strips_metadata(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "sample_shred.jpg"
    assert target.exists()
    data = piexif.load(str(target))
    assert not data.get("0th")


def test_shred_multi_pass(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], passes=3, output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "sample_shred.jpg"
    assert target.exists()


def test_shred_quality(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], quality=85, output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "sample_shred.jpg"
    assert target.exists()


def test_shred_check_reports_clean_file(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], check=True, output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0