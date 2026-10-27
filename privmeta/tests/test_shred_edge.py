import os
import stat
import struct

import piexif
from PIL import Image, PngImagePlugin

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


def _mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def _build_png_with_text(tmp_path):
    path = tmp_path / "meta.png"
    image = Image.new("RGB", (10, 10), color=(120, 120, 120))
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "should be removed")
    info.add_text("Author", "private")
    image.save(str(path), "PNG", pnginfo=info)
    return str(path)


def _png_has_text_chunk(path):
    with open(path, "rb") as handle:
        data = handle.read()
    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        if chunk_type in (b"tEXt", b"zTXt", b"iTXt"):
            return True
        pos += 12 + length
    return False


def _build_webp_with_exif(tmp_path):
    base = tmp_path / "base.webp"
    Image.new("RGB", (10, 10), color=(80, 80, 80)).save(str(base), "WEBP")
    with open(base, "rb") as handle:
        data = handle.read()
    payload = {
        "0th": {piexif.ImageIFD.Make: b"TestMake", piexif.ImageIFD.Model: b"TestModel"},
        "Exif": {},
        "GPS": {},
        "1st": {},
    }
    exif_bytes = piexif.dump(payload)
    exif_chunk = b"EXIF" + struct.pack("<I", len(exif_bytes)) + exif_bytes
    if len(exif_bytes) & 1:
        exif_chunk += b"\x00"
    body = data[12:] + exif_chunk
    target = tmp_path / "meta.webp"
    target.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + b"WEBP" + body)
    return str(target)


def _webp_has_exif_chunk(path):
    with open(path, "rb") as handle:
        data = handle.read()
    pos = 12
    while pos + 8 <= len(data):
        chunk_type = data[pos:pos + 4]
        length = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if chunk_type == b"EXIF":
            return True
        pos += 8 + length + (length & 1)
    return False


def test_shred_strips_png_text_chunks(tmp_path):
    source = _build_png_with_text(tmp_path)
    assert _png_has_text_chunk(source)
    output = tmp_path / "out"
    ns = _args([source], output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "meta_shred.png"
    assert target.exists()
    assert not _png_has_text_chunk(str(target))


def test_shred_strips_webp_exif_chunk(tmp_path):
    source = _build_webp_with_exif(tmp_path)
    assert _webp_has_exif_chunk(source)
    output = tmp_path / "out"
    ns = _args([source], output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "meta_shred.webp"
    assert target.exists()
    assert not _webp_has_exif_chunk(str(target))


def test_shred_multi_pass_leaves_no_temp_files(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], passes=3, output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    assert (output / "sample_shred.jpg").exists()
    leftovers = list(output.glob("*.pass*"))
    assert leftovers == []


def test_shred_inplace_preserves_mode(jpeg_with_exif):
    os.chmod(jpeg_with_exif, 0o640)
    ns = _args([jpeg_with_exif], inplace=True)
    code = shred_cmd.run(ns)
    assert code == 0
    assert _mode(jpeg_with_exif) == 0o640


def test_shred_quality_recompresses_jpeg(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_with_exif], quality=50, output_dir=str(output))
    code = shred_cmd.run(ns)
    assert code == 0
    target = output / "sample_shred.jpg"
    assert target.exists()
    assert target.stat().st_size > 0
