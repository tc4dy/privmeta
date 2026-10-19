from pypdf import PdfReader, PdfWriter

from ..errors import PrivMetaError


def _reset_writer(writer):
    try:
        writer.metadata = None
    except Exception:
        pass
    root = writer.root_object
    for key in ("/Info", "/Metadata"):
        if key in root:
            try:
                del root[key]
            except Exception:
                pass


def strip(source, target):
    try:
        reader = PdfReader(source)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        _reset_writer(writer)
        with open(target, "wb") as handle:
            writer.write(handle)
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