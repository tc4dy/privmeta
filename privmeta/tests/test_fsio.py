import os
import stat

import pytest

from privmeta.errors import PrivMetaError
from privmeta.fsio import atomic_write, backup, collect, resolve_output


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def test_atomic_write_preserves_existing_mode(tmp_path):
    target = tmp_path / "photo.jpg"
    target.write_bytes(b"old")
    os.chmod(target, 0o640)
    atomic_write(str(target), b"new")
    assert target.read_bytes() == b"new"
    assert _mode(str(target)) == 0o640


def test_atomic_write_creates_with_umask(tmp_path):
    target = tmp_path / "fresh.jpg"
    atomic_write(str(target), b"data")
    assert target.read_bytes() == b"data"
    assert _mode(str(target)) != 0o600


def test_atomic_write_replaces_content(tmp_path):
    target = tmp_path / "photo.jpg"
    target.write_bytes(b"x" * 1024)
    atomic_write(str(target), b"short")
    assert target.read_bytes() == b"short"


def test_collect_accepts_literal_path_with_brackets(tmp_path):
    path = tmp_path / "photo[1].jpg"
    path.write_bytes(b"data")
    targets, warnings = collect([str(path)])
    assert targets == [str(path)]
    assert warnings == []


def test_collect_expands_glob_pattern(tmp_path):
    for name in ("a.jpg", "b.jpg", "c.png"):
        (tmp_path / name).write_bytes(b"data")
    targets, _warnings = collect([str(tmp_path / "*.jpg")])
    assert sorted(targets) == sorted(
        [str(tmp_path / "a.jpg"), str(tmp_path / "b.jpg")]
    )


def test_collect_rejects_missing_paths(tmp_path):
    with pytest.raises(PrivMetaError):
        collect([str(tmp_path / "ghost.jpg")])


def test_collect_suggests_quoted_spaces(tmp_path):
    spaced = tmp_path / "my photo.jpg"
    spaced.write_bytes(b"data")
    with pytest.raises(PrivMetaError) as exc_info:
        collect([str(tmp_path / "my"), "photo.jpg"])
    assert "quoting" in str(exc_info.value)


def test_resolve_output_avoids_overwrite(tmp_path):
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    (tmp_path / "photo_cleaned.jpg").write_bytes(b"existing")
    target = resolve_output(str(source))
    assert target == str(tmp_path / "photo_cleaned_1.jpg")


def test_resolve_output_creates_directory(tmp_path):
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    out = tmp_path / "nested" / "out"
    target = resolve_output(str(source), str(out))
    assert os.path.isdir(str(out))
    assert target.startswith(str(out))


def test_backup_writes_identical_copy(tmp_path):
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"payload")
    backup_path = backup(str(source))
    assert backup_path == str(source) + ".bak"
    assert (tmp_path / "photo.jpg.bak").read_bytes() == b"payload"
