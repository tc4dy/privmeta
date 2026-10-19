import glob as globmod
import os
import shutil
import tempfile

from .errors import PrivMetaError


def atomic_write(target, data):
    directory = os.path.dirname(os.path.abspath(target)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".privmeta.")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except Exception:
        _silent_unlink(tmp)
        raise


def atomic_stream(target, writer):
    directory = os.path.dirname(os.path.abspath(target)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".privmeta.")
    try:
        with os.fdopen(fd, "wb") as handle:
            writer(handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except Exception:
        _silent_unlink(tmp)
        raise


def _silent_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def _join_hint(raw):
    joined = " ".join(raw)
    return f"did you mean \"{joined}\"?"


def collect(paths, recursive=False):
    targets = []
    warnings = []
    visited = set()
    raw = list(paths)
    for entry in raw:
        expanded = globmod.glob(os.path.expanduser(entry))
        if not expanded:
            expanded = [os.path.expanduser(entry)]
        for item in expanded:
            if os.path.isdir(item):
                if recursive:
                    for root, _dirs, files in os.walk(item):
                        for name in sorted(files):
                            targets.append(os.path.join(root, name))
                else:
                    for name in sorted(os.listdir(item)):
                        candidate = os.path.join(item, name)
                        if os.path.isfile(candidate):
                            targets.append(candidate)
            elif os.path.isfile(item):
                targets.append(item)
            else:
                warnings.append(f"not found: {item}")
    unique = []
    for path in targets:
        real = os.path.realpath(path)
        if real in visited:
            continue
        visited.add(real)
        unique.append(path)
    if not unique:
        if len(raw) > 1:
            warnings.append(_join_hint(raw))
        raise PrivMetaError(
            "no valid input files; " + "; ".join(warnings) if warnings else "no valid input files"
        )
    return unique, warnings


def resolve_output(source, output_dir=None, suffix="_cleaned"):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base = os.path.basename(source)
        root, ext = os.path.splitext(base)
        candidate = os.path.join(output_dir, f"{root}{suffix}{ext}")
    else:
        directory = os.path.dirname(os.path.abspath(source))
        base = os.path.basename(source)
        root, ext = os.path.splitext(base)
        candidate = os.path.join(directory, f"{root}{suffix}{ext}")
    counter = 1
    original = candidate
    while os.path.exists(candidate) and os.path.abspath(candidate) != os.path.abspath(source):
        root, ext = os.path.splitext(original)
        candidate = f"{root}_{counter}{ext}"
        counter += 1
    return candidate


def backup(path):
    target = path + ".bak"
    shutil.copy2(path, target)
    return target