import shutil
import subprocess

from ..errors import MissingDependency, PrivMetaError


def _ffmpeg():
    binary = shutil.which("ffmpeg")
    if binary is None:
        raise MissingDependency("ffmpeg is not installed or not on PATH")
    return binary


def strip(source, target):
    command = [
        _ffmpeg(),
        "-y",
        "-i",
        source,
        "-map_metadata",
        "-1",
        "-c",
        "copy",
        target,
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise PrivMetaError(f"Cannot execute ffmpeg: {exc}")
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise PrivMetaError(f"ffmpeg failed: {message[:400]}")


def read(source):
    binary = _ffmpeg()
    command = [binary, "-i", source, "-hide_banner", "-f", "ffmetadata", "-"]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        raise PrivMetaError(f"Cannot execute ffmpeg: {exc}")
    if result.returncode != 0:
        raise PrivMetaError(f"ffmpeg could not read {source}")
    info = {}
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        if "=" in line and not line.startswith(";"):
            key, value = line.split("=", 1)
            info[key.strip()] = value.strip()
    return info