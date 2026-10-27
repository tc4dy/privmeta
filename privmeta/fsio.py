import glob as globmod
import os
import shutil
import tempfile

from .errors import PrivMetaError


def _silent_unlink(path):
    try:
        os.unlink(path)
    except OSError:
        pass


def _apply_mode(reference, target):
    try:
        mode = os.stat(reference).st_mode & 0o777
    except OSError:
        current = os.umask(0)
        os.umask(current)
        mode = 0o666 & ~current
    os.chmod(target, mode)


def atomic_write(target, data):
    directory = os.path.dirname(os.path.abspath(target)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".privmeta.")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        _apply_mode(target, tmp)
        os.replace(tmp, target)
    except Exception:
        _silent_unlink(tmp)
        raise


def _expand_entry(entry):
    expanded = os.path.expanduser(entry)
    if os.path.exists(expanded):
        return [expanded]
    matches = globmod.glob(expanded)
    if matches:
        return matches
    return [expanded]


def _join_hint(raw):
    if len(raw) < 2:
        return None
    joined = os.path.expanduser(" ".join(raw))
    if os.path.exists(joined):
        return f'paths contain spaces; try quoting "{joined}"'
    return None


def collect(paths, recursive=False):
    targets = []
    warnings = []
    visited = set()
    raw = list(paths)
    for entry in raw:
        for item in _expand_entry(entry):
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
        hint = _join_hint(raw)
        if hint:
            warnings.append(hint)
        if warnings:
            raise PrivMetaError("no valid input files; " + "; ".join(warnings))
        raise PrivMetaError("no valid input files")
    return unique, warnings


def resolve_output(source, output_dir=None, suffix="_cleaned"):
    base = os.path.basename(source)
    root, ext = os.path.splitext(base)
    if output_dir:
        directory = os.path.expanduser(output_dir)
        os.makedirs(directory, exist_ok=True)
    else:
        directory = os.path.dirname(os.path.abspath(source))
    original = os.path.join(directory, f"{root}{suffix}{ext}")
    candidate = original
    counter = 1
    while os.path.exists(candidate):
        stem, extension = os.path.splitext(original)
        candidate = f"{stem}_{counter}{extension}"
        counter += 1
    return candidate


def backup(path):
    target = path + ".bak"
    shutil.copy2(path, target)
    return target
