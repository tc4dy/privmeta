import zipfile

from ..errors import PrivMetaError

_DROP_PREFIXES = ("docProps/",)


def _should_drop(name):
    return any(name.startswith(prefix) for prefix in _DROP_PREFIXES)


def strip(source, target):
    try:
        with zipfile.ZipFile(source, "r") as source_zip:
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as target_zip:
                for item in source_zip.infolist():
                    if _should_drop(item.filename):
                        continue
                    target_zip.writestr(item, source_zip.read(item.filename))
    except (zipfile.BadZipFile, OSError) as exc:
        raise PrivMetaError(f"Office metadata strip failed: {exc}")


def read(source):
    info = {}
    try:
        with zipfile.ZipFile(source, "r") as archive:
            for name in archive.namelist():
                if name.startswith("docProps/"):
                    info[name] = archive.getinfo(name).file_size
    except (zipfile.BadZipFile, OSError) as exc:
        raise PrivMetaError(f"Cannot read Office archive: {exc}")
    return info