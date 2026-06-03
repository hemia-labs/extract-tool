import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from app.extractors.base import BaseExtractor, ExtractionResult
from app.extractors.xlsx_extractor import XlsxExtractor
from app.utils.errors import ExtractionFailedError


class NumbersExtractor(BaseExtractor):
    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            raise ExtractionFailedError("LibreOffice is required to extract .numbers files")

        with TemporaryDirectory() as temp_dir:
            command = [
                soffice,
                "--headless",
                "--convert-to",
                "xlsx",
                "--outdir",
                temp_dir,
                str(path),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise ExtractionFailedError(
                    f"Failed to convert .numbers file: {completed.stderr or completed.stdout}"
                )

            converted_files = list(Path(temp_dir).glob("*.xlsx"))
            if not converted_files:
                raise ExtractionFailedError("Failed to convert .numbers file to .xlsx")

            result = XlsxExtractor().extract(converted_files[0], ocr=ocr, language=language, output=output)
            result["metadata"]["sourceFormat"] = "numbers"
            return result
