import shutil

from ..errors import PrivMetaError

try:
    from mutagen import File as MutagenFile
    from mutagen.flac import FLAC
    from mutagen.id3 import ID3
except ImportError:
    MutagenFile = None
    FLAC = None
    ID3 = None


def _require():
    if MutagenFile is None:
        raise PrivMetaError("mutagen is not installed")


def strip(source, target):
    _require()
    shutil.copy2(source, target)
    try:
        audio = MutagenFile(target)
        if audio is None:
            raise PrivMetaError("Unsupported audio container")
        if audio.tags is not None:
            audio.delete()
            audio.save()
    except Exception as exc:
        raise PrivMetaError(f"Audio metadata strip failed: {exc}")


def read(source):
    _require()
    info = {}
    try:
        audio = MutagenFile(source)
        if audio is None:
            raise PrivMetaError("Unsupported audio container")
        if audio.tags:
            for key in audio.tags:
                info[str(key)] = str(audio.tags[key])
        info["format"] = type(audio).__name__
    except Exception as exc:
        raise PrivMetaError(f"Cannot read audio metadata: {exc}")
    return info