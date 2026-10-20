import struct

from ..errors import PrivMetaError, UnsupportedFormat
from ..fsio import atomic_write
from ..sniff import detect, IMAGE

JPEG_SOI = b"\xff\xd8"
JPEG_SOS = 0xDA
JPEG_EOI = 0xD9

APP1 = 0xE1
APP2 = 0xE2
APP13 = 0xED
COM = 0xFE

XMP_HEADER = b"http://ns.adobe.com/xap/1.0/\x00"
XMP_EXT_HEADER = b"http://ns.adobe.com/xmp/extension/"
ICC_HEADER = b"ICC_PROFILE\x00"
IPTC_HEADER = b"Photoshop 3.0"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_TEXT_CHUNKS = {b"tEXt", b"zTXt", b"iTXt"}
PNG_ICC_CHUNK = b"iCCP"
PNG_EXIF_CHUNK = b"eXIf"

WEBP_RIFF = b"RIFF"
WEBP_FORM = b"WEBP"
WEBP_METADATA_CHUNKS = {b"EXIF", b"XMP ", b"ICCP"}


def _segment_label(marker, body):
    head = body[:32]
    if marker == APP1 and head.startswith(b"Exif\x00"):
        return "exif"
    if marker == APP1 and head.startswith(XMP_HEADER):
        return "xmp"
    if marker == APP1 and head.startswith(XMP_EXT_HEADER):
        return "xmp"
    if marker == APP2 and head.startswith(ICC_HEADER):
        return "icc"
    if marker == APP13 and head.startswith(IPTC_HEADER):
        return "iptc"
    if marker == COM:
        return "comment"
    return None


def _walk_jpeg(data):
    if not data.startswith(JPEG_SOI):
        raise UnsupportedFormat("Not a JPEG file")
    pos = 2
    total = len(data)
    while pos < total:
        if data[pos] != 0xFF:
            raise PrivMetaError(f"Corrupt JPEG segment at offset {pos}")
        while pos < total and data[pos] == 0xFF:
            pos += 1
        if pos >= total:
            raise PrivMetaError("Truncated JPEG marker")
        marker = data[pos]
        pos += 1
        if marker == JPEG_EOI:
            yield marker, None, pos - 2, pos
            return
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            yield marker, b"", pos - 2, pos
            continue
        if marker == JPEG_SOS:
            yield marker, None, pos - 2, total
            return
        if pos + 2 > total:
            raise PrivMetaError("Truncated JPEG segment length")
        length = struct.unpack(">H", data[pos:pos + 2])[0]
        end = pos + length
        if end > total or length < 2:
            raise PrivMetaError(f"Invalid JPEG segment length at offset {pos - 2}")
        body = data[pos + 2:end]
        yield marker, body, pos - 2, end
        pos = end


def inspect_jpeg(path):
    with open(path, "rb") as handle:
        data = handle.read()
    found = []
    for marker, body, _start, _end in _walk_jpeg(data):
        if body is None:
            break
        label = _segment_label(marker, body)
        if label:
            found.append(label)
    return found


def _strip_jpeg(source, target, drop_xmp=True, drop_iptc=True, drop_icc=True, drop_comments=True):
    with open(source, "rb") as handle:
        data = handle.read()
    output = bytearray(JPEG_SOI)
    dropped = []
    last_end = 2
    for marker, body, start, end in _walk_jpeg(data):
        if body is None:
            output.extend(data[start:end])
            last_end = end
            if marker == JPEG_SOS:
                break
            continue
        label = _segment_label(marker, body)
        drop = False
        if label == "xmp" and drop_xmp:
            drop = True
        elif label == "iptc" and drop_iptc:
            drop = True
        elif label == "icc" and drop_icc:
            drop = True
        elif label == "comment" and drop_comments:
            drop = True
        if drop:
            dropped.append(label)
        else:
            output.extend(data[start:end])
        last_end = end
    if last_end < len(data):
        output.extend(data[last_end:])
    atomic_write(target, bytes(output))
    return dropped


def inspect_png(path):
    found = []
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith(PNG_SIGNATURE):
        raise UnsupportedFormat("Not a PNG file")
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        if chunk_type in PNG_TEXT_CHUNKS:
            found.append("text")
        elif chunk_type == PNG_ICC_CHUNK:
            found.append("icc")
        elif chunk_type == PNG_EXIF_CHUNK:
            found.append("exif")
        pos += 12 + length
    return found


def _strip_png(source, target, drop_text=True, drop_icc=True, drop_exif=False, drop_xmp=True):
    with open(source, "rb") as handle:
        data = handle.read()
    if not data.startswith(PNG_SIGNATURE):
        raise UnsupportedFormat("Not a PNG file")
    output = bytearray(PNG_SIGNATURE)
    dropped = []
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk = data[pos:pos + 12 + length]
        drop = False
        if chunk_type == b"iTXt":
            if drop_xmp and b"XML:com.adobe.xmp" in chunk:
                drop = True
            elif drop_text and b"XML:com.adobe.xmp" not in chunk:
                drop = True
        elif chunk_type in (b"tEXt", b"zTXt") and drop_text:
            drop = True
        elif chunk_type == PNG_ICC_CHUNK and drop_icc:
            drop = True
        elif chunk_type == PNG_EXIF_CHUNK and drop_exif:
            drop = True
        if drop:
            dropped.append(chunk_type.decode("ascii", errors="replace").strip("\x00"))
        else:
            output.extend(chunk)
        pos += 12 + length
        if chunk_type == b"IEND":
            break
    atomic_write(target, bytes(output))
    return dropped


def inspect_webp(path):
    found = []
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith(WEBP_RIFF) or data[8:12] != WEBP_FORM:
        raise UnsupportedFormat("Not a WebP file")
    pos = 12
    while pos + 8 <= len(data):
        chunk_type = data[pos:pos + 4]
        length = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        if chunk_type in WEBP_METADATA_CHUNKS:
            found.append(chunk_type.decode("ascii", errors="replace").strip("\x00"))
        pos += 8 + length + (length & 1)
    return found


def _strip_webp(source, target, drop_exif=True, drop_xmp=True, drop_icc=True):
    with open(source, "rb") as handle:
        data = handle.read()
    if not data.startswith(WEBP_RIFF) or data[8:12] != WEBP_FORM:
        raise UnsupportedFormat("Not a WebP file")
    chunks = bytearray()
    dropped = []
    pos = 12
    while pos + 8 <= len(data):
        chunk_type = data[pos:pos + 4]
        length = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        total = 8 + length + (length & 1)
        chunk = data[pos:pos + total]
        drop = False
        if chunk_type == b"EXIF" and drop_exif:
            drop = True
        elif chunk_type == b"XMP " and drop_xmp:
            drop = True
        elif chunk_type == b"ICCP" and drop_icc:
            drop = True
        if drop:
            dropped.append(chunk_type.decode("ascii", errors="replace").strip("\x00"))
        else:
            chunks.extend(chunk)
        pos += total
    header = bytearray(WEBP_RIFF)
    header.extend(struct.pack("<I", 4 + len(chunks)))
    header.extend(WEBP_FORM)
    header.extend(chunks)
    atomic_write(target, bytes(header))
    return dropped


def xmp_strip(source, target, drop_xmp=True, drop_iptc=True, drop_icc=True, drop_comments=True, drop_exif=False):
    family, label = detect(source)
    if family != IMAGE:
        raise UnsupportedFormat(f"Metadata strip is not supported for {label}")
    if label == "jpeg":
        return _strip_jpeg(source, target, drop_xmp, drop_iptc, drop_icc, drop_comments)
    if label == "png":
        return _strip_png(source, target, drop_comments, drop_icc, drop_exif, drop_xmp)
    if label == "webp":
        return _strip_webp(source, target, drop_exif, drop_xmp, drop_icc)
    raise UnsupportedFormat(f"Metadata strip is not supported for {label}")


def xmp_inspect(source):
    family, label = detect(source)
    if family != IMAGE:
        raise UnsupportedFormat(f"Inspection is not supported for {label}")
    if label == "jpeg":
        return inspect_jpeg(source)
    if label == "png":
        return inspect_png(source)
    if label == "webp":
        return inspect_webp(source)
    raise UnsupportedFormat(f"Inspection is not supported for {label}")


def get_exif_bytes(path):
    family, label = detect(path)
    if label == "png":
        with open(path, "rb") as handle:
            data = handle.read()
        pos = len(PNG_SIGNATURE)
        while pos + 8 <= len(data):
            length = struct.unpack(">I", data[pos:pos + 4])[0]
            chunk_type = data[pos + 4:pos + 8]
            if chunk_type == PNG_EXIF_CHUNK:
                return data[pos + 8:pos + 8 + length]
            pos += 12 + length
    elif label == "webp":
        with open(path, "rb") as handle:
            data = handle.read()
        pos = 12
        while pos + 8 <= len(data):
            chunk_type = data[pos:pos + 4]
            length = struct.unpack("<I", data[pos + 4:pos + 8])[0]
            if chunk_type == b"EXIF":
                return data[pos + 8:pos + 8 + length]
            pos += 8 + length + (length & 1)
    return None
