try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version
    try:
        __version__ = _pkg_version("privmeta")
    except PackageNotFoundError:
        __version__ = "0.1.3"
except ImportError:
    __version__ = "0.1.3"
