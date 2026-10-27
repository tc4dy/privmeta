import piexif

from privmeta.commands import fake as fake_cmd


def _args(paths, **overrides):
    ns = type("Args", (), {})()
    ns.paths = paths
    ns.camera = overrides.get("camera")
    ns.city = overrides.get("city")
    ns.radius = overrides.get("radius")
    ns.date_range = overrides.get("date_range")
    ns.timeline = overrides.get("timeline", False)
    ns.preserve = overrides.get("preserve", False)
    ns.thumbnail = overrides.get("thumbnail", False)
    ns.seed = overrides.get("seed")
    ns.recursive = overrides.get("recursive", False)
    ns.output_dir = overrides.get("output_dir")
    ns.inplace = overrides.get("inplace", False)
    ns.fail_fast = overrides.get("fail_fast", False)
    return ns


def _lens_name(exif_data):
    raw = exif_data["Exif"].get(piexif.ExifIFD.LensModel)
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


def _focal_mm(exif_data):
    value = exif_data["Exif"][piexif.ExifIFD.FocalLength]
    return value[0] / value[1] if value[1] else 0.0


def test_fake_replaces_exif(jpeg_clean, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_clean], camera="sony_a7iv", output_dir=str(output), seed=1)
    code = fake_cmd.run(ns)
    assert code == 0
    target = output / "clean_faked.jpg"
    data = piexif.load(str(target))
    assert data["0th"][piexif.ImageIFD.Make] == b"SONY"


def test_fake_with_gps(jpeg_clean, tmp_path):
    output = tmp_path / "out"
    ns = _args(
        [jpeg_clean],
        camera="sony_a7iv",
        city="istanbul",
        output_dir=str(output),
        seed=2,
    )
    code = fake_cmd.run(ns)
    assert code == 0
    target = output / "clean_faked.jpg"
    data = piexif.load(str(target))
    assert data.get("GPS")


def test_fake_rejects_unknown_camera(jpeg_clean, tmp_path):
    output = tmp_path / "out"
    ns = _args([jpeg_clean], camera="not_a_camera", output_dir=str(output))
    code = fake_cmd.run(ns)
    assert code == 2


def test_fake_preserve(jpeg_with_exif, tmp_path):
    output = tmp_path / "out"
    ns = _args(
        [jpeg_with_exif],
        camera="sony_a7iv",
        preserve=True,
        output_dir=str(output),
        seed=3,
    )
    code = fake_cmd.run(ns)
    assert code == 0
    target = output / "sample_faked.jpg"
    data = piexif.load(str(target))
    assert data["0th"][piexif.ImageIFD.Make] == b"SONY"


def test_fake_prime_lens_produces_prime_focal(jpeg_clean, tmp_path):
    output = tmp_path / "out"
    for seed in range(1, 6):
        ns = _args(
            [jpeg_clean],
            camera="leica_q2",
            output_dir=str(output / f"s{seed}"),
            seed=seed,
        )
        code = fake_cmd.run(ns)
        assert code == 0
        target = output / f"s{seed}" / "clean_faked.jpg"
        data = piexif.load(str(target))
        assert _focal_mm(data) == 28


def test_fake_focal_always_within_selected_lens_range(jpeg_clean, tmp_path):
    lenses = fake_cmd._load_json("lenses.json")
    output = tmp_path / "out"
    for seed in range(1, 21):
        ns = _args(
            [jpeg_clean],
            camera="sony_a1",
            output_dir=str(output / f"s{seed}"),
            seed=seed,
        )
        code = fake_cmd.run(ns)
        assert code == 0
        target = output / f"s{seed}" / "clean_faked.jpg"
        data = piexif.load(str(target))
        focal = _focal_mm(data)
        lens_name = _lens_name(data)
        matched = None
        for candidate in lenses["sony_a1"]:
            if candidate["name"] == lens_name:
                matched = candidate
                break
        assert matched is not None, f"lens {lens_name} not in profile"
        assert matched["focal_min"] <= focal <= matched["focal_max"]
