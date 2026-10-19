import os
import sys

from .commands import clean, fake, info, shred
from .output import ask, fail, info, ok


_OPTIONS = [
    ("clean", "Clean", "strip metadata from files"),
    ("fake", "Fake", "inject a camera profile and GPS"),
    ("shred", "Shred", "overwrite metadata traces"),
    ("info", "Info", "inspect what a file carries"),
    ("exit", "Exit", ""),
]

_ALIASES = {
    "1": "clean", "2": "fake", "3": "shred", "4": "info", "5": "exit",
    "c": "clean", "clean": "clean",
    "f": "fake", "fake": "fake",
    "s": "shred", "shred": "shred",
    "i": "info", "info": "info",
    "e": "exit", "exit": "exit", "q": "exit", "quit": "exit",
}


def _menu():
    ask("Select Option (1, 2, 3...)")
    sys.stdout.write("\n")
    for index, (keyword, label, desc) in enumerate(_OPTIONS, start=1):
        if desc:
            info(f"  {index}- {label} ({desc})")
        else:
            info(f"  {index}- {label}")
    sys.stdout.write("\n")


def _read_choice():
    prompt = "\033[36m›\033[0m " if sys.stdout.isatty() else "› "
    try:
        raw = input(prompt).strip().lower()
    except EOFError:
        return None
    if not raw:
        return None
    return _ALIASES.get(raw)


def _paths():
    raw = input("  path › ").strip()
    if not raw:
        fail("no path given")
        return []
    return raw.split()


def _clean_args():
    namespace = type("Args", (), {})()
    namespace.paths = _paths()
    if not namespace.paths:
        return None
    namespace.all_fields = True
    namespace.drop = None
    namespace.keep = None
    namespace.recursive = False
    namespace.output_dir = None
    namespace.inplace = False
    namespace.keep_backup = False
    namespace.rename = False
    namespace.reset_time = False
    namespace.dry_run = False
    namespace.fail_fast = False
    return namespace


def _fake_args():
    namespace = type("Args", (), {})()
    namespace.paths = _paths()
    if not namespace.paths:
        return None
    namespace.camera = None
    namespace.city = None
    namespace.radius = None
    namespace.date_range = None
    namespace.timeline = False
    namespace.preserve = False
    namespace.thumbnail = False
    namespace.seed = None
    namespace.recursive = False
    namespace.output_dir = None
    namespace.inplace = False
    namespace.fail_fast = False
    return namespace


def _shred_args():
    namespace = type("Args", (), {})()
    namespace.paths = _paths()
    if not namespace.paths:
        return None
    namespace.passes = 1
    namespace.quality = None
    namespace.check = True
    namespace.recursive = False
    namespace.output_dir = None
    namespace.inplace = False
    namespace.fail_fast = False
    return namespace


def _info_args():
    namespace = type("Args", (), {})()
    namespace.paths = _paths()
    if not namespace.paths:
        return None
    namespace.recursive = False
    return namespace


def launch():
    _menu()
    try:
        choice = _read_choice()
    except KeyboardInterrupt:
        return
    if choice is None:
        fail("invalid option")
        return
    if choice == "exit":
        ok("bye")
        return
    if choice == "clean":
        namespace = _clean_args()
        if namespace:
            clean.run(namespace)
    elif choice == "fake":
        namespace = _fake_args()
        if namespace:
            fake.run(namespace)
    elif choice == "shred":
        namespace = _shred_args()
        if namespace:
            shred.run(namespace)
    elif choice == "info":
        namespace = _info_args()
        if namespace:
            info.run(namespace)
    ok("done")