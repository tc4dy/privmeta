import zipfile
import xml.etree.ElementTree as ET

from ..errors import PrivMetaError

_NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
_DROP_PREFIX = "docProps/"
_REL_TYPES = (
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
    "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail",
)
_ROOT_RELS = "_rels/.rels"
_CONTENT_TYPES = "[Content_Types].xml"


def _should_drop(name):
    return name.startswith(_DROP_PREFIX)


def _prune_rels(data):
    root = ET.fromstring(data)
    for parent in root:
        for child in list(parent):
            rel_type = child.get("Type", "")
            target = child.get("Target", "")
            if rel_type in _REL_TYPES or target.startswith(_DROP_PREFIX):
                parent.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _prune_content_types(data):
    root = ET.fromstring(data)
    for child in list(root):
        part_name = child.get("PartName", "")
        if part_name.startswith("/" + _DROP_PREFIX):
            root.remove(child)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _transform(name, payload):
    if name == _ROOT_RELS:
        return _prune_rels(payload)
    if name == _CONTENT_TYPES:
        return _prune_content_types(payload)
    return payload


def strip(source, target):
    try:
        with zipfile.ZipFile(source, "r") as source_zip:
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as target_zip:
                for item in source_zip.infolist():
                    if _should_drop(item.filename):
                        continue
                    payload = source_zip.read(item.filename)
                    payload = _transform(item.filename, payload)
                    target_zip.writestr(item, payload)
    except (zipfile.BadZipFile, OSError, ET.ParseError) as exc:
        raise PrivMetaError(f"Office metadata strip failed: {exc}")


def read(source):
    info = {}
    try:
        with zipfile.ZipFile(source, "r") as archive:
            for name in archive.namelist():
                if name.startswith(_DROP_PREFIX):
                    info[name] = archive.getinfo(name).file_size
    except (zipfile.BadZipFile, OSError) as exc:
        raise PrivMetaError(f"Cannot read Office archive: {exc}")
    return info
