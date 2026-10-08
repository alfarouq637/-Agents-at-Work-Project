"""Shared validation and bounded parsing for user supplied uploads."""

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_TELEGRAM_ATTACHMENT_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_PDF_PAGES_TO_EXTRACT = 50
MAX_EXTRACTED_TEXT_CHARS = 50_000

ALLOWED_UPLOADS = {
    ".jpg": ("image", b"\xff\xd8\xff"),
    ".jpeg": ("image", b"\xff\xd8\xff"),
    ".png": ("image", b"\x89PNG\r\n\x1a\n"),
    ".webp": ("image", b"RIFF"),
    ".pdf": ("pdf", b"%PDF-"),
}

IMAGE_FORMATS_BY_EXTENSION = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
}

IMAGE_MEDIA_TYPES_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# Reject decompression bombs before image pixels are fully decoded.
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def sanitize_image_upload(content_bytes: bytes, extension: str) -> bytes:
    """Decode, size-limit, orient, and re-encode an allowed image without metadata."""
    expected_format = IMAGE_FORMATS_BY_EXTENSION.get(extension)
    if not expected_format:
        raise ValueError("Unsupported image type")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content_bytes)) as original:
                if original.format != expected_format:
                    raise ValueError("Image data does not match its declared type")
                original.load()
                if original.width * original.height > MAX_IMAGE_PIXELS:
                    raise ValueError("Image has too many pixels")
                image = ImageOps.exif_transpose(original)
                if expected_format == "JPEG" and image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                elif expected_format == "WEBP" and image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

                sanitized = io.BytesIO()
                save_options = {"format": expected_format, "exif": b"", "icc_profile": None}
                if expected_format == "JPEG":
                    save_options.update({"quality": 90, "optimize": True, "progressive": True})
                elif expected_format == "PNG":
                    save_options.update({"optimize": True})
                else:
                    save_options.update({"quality": 90, "method": 4, "xmp": b""})
                image.save(sanitized, **save_options)
                return sanitized.getvalue()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        ValueError,
    ) as exc:
        raise ValueError("Image could not be safely processed") from exc


def extract_pdf_text(content_bytes: bytes) -> str:
    """Extract a bounded amount of PDF text without retaining the source file."""
    try:
        import fitz

        document = fitz.open(stream=content_bytes, filetype="pdf")
        try:
            pages_text = []
            total_chars = 0
            for page_number, page in enumerate(document):
                if page_number >= MAX_PDF_PAGES_TO_EXTRACT:
                    break
                page_text = page.get_text() or ""
                if page_text:
                    remaining = MAX_EXTRACTED_TEXT_CHARS - total_chars
                    pages_text.append(page_text[:remaining])
                    total_chars += min(len(page_text), remaining)
                    if total_chars >= MAX_EXTRACTED_TEXT_CHARS:
                        break
            return "\n".join(pages_text).strip()[:MAX_EXTRACTED_TEXT_CHARS]
        finally:
            document.close()
    except Exception:
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            chunks = []
            total_chars = 0
            for page in reader.pages[:MAX_PDF_PAGES_TO_EXTRACT]:
                page_text = page.extract_text() or ""
                remaining = MAX_EXTRACTED_TEXT_CHARS - total_chars
                chunks.append(page_text[:remaining])
                total_chars += min(len(page_text), remaining)
                if total_chars >= MAX_EXTRACTED_TEXT_CHARS:
                    break
            return "\n".join(chunks).strip()[:MAX_EXTRACTED_TEXT_CHARS]
        except Exception:
            return "(Unable to extract text from this PDF.)"
