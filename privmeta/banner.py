import os
import sys

from . import __version__


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def _visible_len(text):
    result = 0
    index = 0
    while index < len(text):
        if text[index] == "\033":
            end = text.find("m", index)
            if end == -1:
                break
            index = end + 1
        else:
            result += 1
            index += 1
    return result


def _center_ansi(text, width):
    visible = _visible_len(text)
    if visible >= width:
        return text
    left = (width - visible) // 2
    right = width - visible - left
    return " " * left + text + " " * right


def show():
    color = _supports_color()
    rule = "─" * 38
    if color:
        rule_line = f"\033[36m{rule}\033[0m"
        title_line = f"\033[1;36mPrivMeta\033[0m \033[90mEXIF/Metadata Privacy Tool\033[0m"
        meta_line = f"\033[38;5;208mv{__version__}\033[0m \033[90m|\033[0m \033[32mgithub.com/tc4dy\033[0m"
    else:
        rule_line = rule
        title_line = "PrivMeta EXIF/Metadata Privacy Tool"
        meta_line = f"v{__version__} | github.com/tc4dy"
    sys.stdout.write("\n")
    sys.stdout.write(rule_line + "\n")
    sys.stdout.write(_center_ansi(title_line, 38) + "\n")
    sys.stdout.write(rule_line + "\n")
    sys.stdout.write(_center_ansi(meta_line, 38) + "\n")
    sys.stdout.write("\n")