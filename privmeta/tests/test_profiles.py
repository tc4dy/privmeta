from privmeta.commands import fake as fake_cmd

REQUIRED_CAMERA_KEYS = {
    "make",
    "model",
    "software",
    "isos",
    "apertures",
    "shutters",
    "focal_min",
    "focal_max",
}
REQUIRED_LENS_KEYS = {"name", "focal_min", "focal_max", "aperture_max"}
REQUIRED_CITY_KEYS = {"lat", "lon", "alt", "radius_km"}


def _load(name):
    return fake_cmd._load_json(name)


def test_camera_profiles_have_required_fields():
    cameras = _load("cameras.json")
    assert len(cameras) >= 35
    for key, camera in cameras.items():
        missing = REQUIRED_CAMERA_KEYS - camera.keys()
        assert not missing, f"{key} missing {missing}"
        assert camera["focal_min"] <= camera["focal_max"], key
        assert all(iso > 0 for iso in camera["isos"]), key
        assert all(a > 0 for a in camera["apertures"]), key
        assert all(s > 0 for s in camera["shutters"]), key


def test_every_camera_has_at_least_one_lens():
    cameras = _load("cameras.json")
    lenses = _load("lenses.json")
    for key in cameras:
        assert key in lenses, f"camera {key} has no lens entry"
        assert len(lenses[key]) >= 1, f"camera {key} has empty lens list"


def test_lens_entries_reference_known_cameras():
    cameras = _load("cameras.json")
    lenses = _load("lenses.json")
    for key in lenses:
        assert key in cameras, f"lens profile {key} has no camera"


def test_lens_fields_are_valid():
    lenses = _load("lenses.json")
    for camera_key, options in lenses.items():
        for lens in options:
            missing = REQUIRED_LENS_KEYS - lens.keys()
            assert not missing, f"{camera_key} lens missing {missing}"
            assert lens["focal_min"] <= lens["focal_max"]
            assert lens["aperture_max"] > 0


def test_lens_focal_range_overlaps_camera_range():
    cameras = _load("cameras.json")
    lenses = _load("lenses.json")
    for key, options in lenses.items():
        camera = cameras[key]
        covered = False
        for lens in options:
            if (
                lens["focal_min"] <= camera["focal_max"]
                and lens["focal_max"] >= camera["focal_min"]
            ):
                covered = True
                break
        assert covered, f"{key} lens range does not overlap camera range"


def test_city_profiles_have_required_fields():
    cities = _load("cities.json")
    assert len(cities) >= 70
    for key, city in cities.items():
        missing = REQUIRED_CITY_KEYS - city.keys()
        assert not missing, f"{key} missing {missing}"
        assert -90.0 <= city["lat"] <= 90.0, key
        assert -180.0 <= city["lon"] <= 180.0, key
        assert city["radius_km"] > 0, key
