import os
import sys


def _use_color():
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _emit(prefix, message, code):
    if _use_color():
        sys.stdout.write(f"\033[{code}m{prefix}\033[0m {message}\n")
    else:
        sys.stdout.write(f"{prefix} {message}\n")


def info(message):
    _emit("[>]", message, "36")


def ok(message):
    _emit("[+]", message, "32")


def warn(message):
    _emit("[!]", message, "33")


def fail(message):
    _emit("[-]", message, "31")


def ask(message):
    _emit("[?]", message, "35")