import datetime
import os
import stat

from privmeta.commands import clean as clean_cmd


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


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def test_clean_inplace_preserves_mode(jpeg_with_exif):
    os.chmod(jpeg_with_exif, 0o640)
    ns = _args([jpeg_with_exif], inplace=True)
    code = clean_cmd.run(ns)
    assert code == 0
    assert _mode(jpeg_with_exif) == 0o640


def test_clean_output_inherits_source_mode(jpeg_with_exif, tmp_path):
    os.chmod(jpeg_with_exif, 0o640)
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output))
    code = clean_cmd.run(ns)
    assert code == 0
    target = output / "sample_cleaned.jpg"
    assert _mode(str(target)) == 0o640


def test_clean_keep_backup_writes_bak(jpeg_with_exif):
    ns = _args([jpeg_with_exif], inplace=True, keep_backup=True)
    code = clean_cmd.run(ns)
    assert code == 0
    assert os.path.exists(jpeg_with_exif + ".bak")


def test_clean_rename_produces_neutral_name(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output), rename=True)
    code = clean_cmd.run(ns)
    assert code == 0
    assert (output / "photo_0001.jpg").exists()


def test_clean_reset_time_sets_uniform_stamp(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output), reset_time=True)
    code = clean_cmd.run(ns)
    assert code == 0
    target = output / "sample_cleaned.jpg"
    mtime = os.stat(str(target)).st_mtime
    expected = datetime.datetime(2020, 1, 1, 12, 0, 0).timestamp()
    assert abs(mtime - expected) < 1.0


def test_clean_dry_run_writes_nothing(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], output_dir=str(output), dry_run=True)
    code = clean_cmd.run(ns)
    assert code == 0
    if output.exists():
        assert list(output.iterdir()) == []
