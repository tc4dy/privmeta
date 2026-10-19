import io

from PIL import Image

from ..errors import PrivMetaError


def create(path, size=(160, 120), quality=85):
    try:
        with Image.open(path) as image:
            image.thumbnail(size)
            buffer = io.BytesIO()
            image.convert("RGB").save(buffer, format="JPEG", quality=quality)
            return buffer.getvalue()
    except OSError as exc:
        raise PrivMetaError(f"Cannot create thumbnail for {path}: {exc}")