from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from app.config import get_settings
from app.utils.errors import FileTooLargeError


async def save_upload_to_temp(upload: UploadFile, suffix: str) -> Path:
    settings = get_settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    with NamedTemporaryFile(delete=False, dir=settings.temp_dir, suffix=suffix) as temp:
        while chunk := await upload.read(1024 * 1024):
            total += len(chunk)
            if total > settings.max_file_size_bytes:
                Path(temp.name).unlink(missing_ok=True)
                raise FileTooLargeError(f"File exceeds {settings.max_file_size_mb} MB limit")
            temp.write(chunk)
        return Path(temp.name)
