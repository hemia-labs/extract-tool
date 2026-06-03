import mimetypes
from pathlib import Path
from typing import Optional

try:
    import magic
except ImportError:
    magic = None

from app.utils.errors import UnsupportedFileTypeError

SUPPORTED_EXTENSIONS = {
    "pdf",
    "txt",
    "md",
    "numbers",
    "docx",
    "xlsx",
    "csv",
    "jpg",
    "jpeg",
    "png",
    "webp",
    "tiff",
}

EXTENSION_MIME_HINTS = {
    "pdf": {"application/pdf"},
    "txt": {"text/plain"},
    "md": {"text/plain", "text/markdown"},
    "numbers": {
        "application/vnd.apple.numbers",
        "application/x-iwork-numbers-sffnumbers",
        "application/zip",
        "application/octet-stream",
    },
    "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "csv": {"text/csv", "text/plain"},
    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "webp": {"image/webp"},
    "tiff": {"image/tiff"},
}


def detect_file(path: Path, filename: Optional[str]) -> tuple[str, str]:
    extension = _extension(filename)
    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"Unsupported file extension: {extension or 'unknown'}")

    mime_type = _mime_type(path, filename)
    allowed = EXTENSION_MIME_HINTS[extension]

    # Office files may be reported as generic zip by libmagic.
    if extension in {"docx", "xlsx"} and mime_type == "application/zip":
        return extension, EXTENSION_MIME_HINTS[extension].copy().pop()

    # Empty/plain text detection can vary across systems.
    if extension in {"txt", "md", "csv"} and mime_type in {"application/octet-stream", "text/plain"}:
        return extension, "text/plain" if extension != "csv" else "text/csv"

    if mime_type not in allowed:
        raise UnsupportedFileTypeError(
            f"MIME type {mime_type} does not match supported extension .{extension}"
        )

    return extension, mime_type


def _extension(filename: Optional[str]) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def _mime_type(path: Path, filename: Optional[str]) -> str:
    if magic is not None:
        return magic.from_file(str(path), mime=True) or "application/octet-stream"
    guessed, _ = mimetypes.guess_type(filename or path.name)
    return guessed or "application/octet-stream"
