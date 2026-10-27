import shutil

from ..errors import PrivMetaError

try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None


def _require():
    if MutagenFile is None:
        raise PrivMetaError("mutagen is not installed")


def strip(source, target):
    _require()
    shutil.copy2(source, target)
    try:
        audio = MutagenFile(target)
    except Exception as exc:
        raise PrivMetaError(f"Cannot open audio file {target}: {exc}")
    if audio is None:
        raise PrivMetaError(f"Unsupported audio container: {target}")
    if audio.tags is None:
        return
    try:
        audio.delete()
    except Exception as exc:
        raise PrivMetaError(f"Audio metadata strip failed: {exc}")


def read(source):
    _require()
    info = {}
    try:
        audio = MutagenFile(source)
    except Exception as exc:
        raise PrivMetaError(f"Cannot read audio metadata: {exc}")
    if audio is None:
        raise PrivMetaError(f"Unsupported audio container: {source}")
    if audio.tags:
        for key in audio.tags:
            info[str(key)] = str(audio.tags[key])
    info["format"] = type(audio).__name__
    return info
