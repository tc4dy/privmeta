from pypdf import PdfReader, PdfWriter

from ..errors import PrivMetaError

_TRANSIENT_INFO = "/Info"
_CATALOG_KEYS = ("/Metadata", "/PieceInfo")


def _drop_from_catalog(writer):
    root = writer.root_object
    for key in _CATALOG_KEYS:
        if key in root:
            try:
                del root[key]
            except Exception:
                pass


def _scrub_trailer(path):
    reader = PdfReader(path)
    trailer = reader.trailer
    if _TRANSIENT_INFO in trailer:
        try:
            del trailer[_TRANSIENT_INFO]
        except Exception:
            pass
    root = reader.root_object
    for key in _CATALOG_KEYS:
        if key in root:
            try:
                del root[key]
            except Exception:
                pass
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.metadata = None
    with open(path, "wb") as handle:
        writer.write(handle)


def strip(source, target):
    try:
        reader = PdfReader(source)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.metadata = None
        _drop_from_catalog(writer)
        with open(target, "wb") as handle:
            writer.write(handle)
        _scrub_trailer(target)
    except Exception as exc:
        raise PrivMetaError(f"PDF metadata strip failed: {exc}")


def read(source):
    try:
        reader = PdfReader(source)
    except Exception as exc:
        raise PrivMetaError(f"Cannot read PDF: {exc}")
    info = {}
    if reader.metadata:
        for key in reader.metadata:
            info[key] = str(reader.metadata[key])
    try:
        if reader.xmp_metadata:
            info["XMP"] = "present"
    except Exception:
        pass
    return info
