from pathlib import Path
from time import perf_counter
from typing import Optional

from fastapi import UploadFile

from app.config import get_settings
from app.extractors.csv_extractor import CsvExtractor
from app.extractors.docx_extractor import DocxExtractor
from app.extractors.image_extractor import ImageExtractor
from app.extractors.numbers_extractor import NumbersExtractor
from app.extractors.pdf_extractor import PdfExtractor
from app.extractors.text_extractor import TextExtractor
from app.extractors.xlsx_extractor import XlsxExtractor
from app.schemas.chunk import Chunk
from app.schemas.extract_response import ExtractMetadata, ExtractResponse
from app.schemas.page_result import PageResult
from app.services.chunk_parser import parse_chunks
from app.services.mime_detector import detect_file
from app.services.text_normalizer import join_pages, normalize_text
from app.utils.errors import ExtractionFailedError
from app.utils.temp_files import save_upload_to_temp


class ExtractionService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def extract(
        self,
        upload: UploadFile,
        ocr: str = "auto",
        language: Optional[str] = None,
        output: str = "text",
    ) -> ExtractResponse:
        filename = Path(upload.filename or "upload").name
        suffix = Path(filename).suffix
        language = language or self.settings.ocr_default_language
        started = perf_counter()
        temp_path = await save_upload_to_temp(upload, suffix=suffix)

        try:
            extension, mime_type = detect_file(temp_path, filename)
            extractor = self._extractor_for(extension)
            result = extractor.extract(temp_path, ocr=ocr, language=language, output=output)
            chunks_mode = output == "chunks"
            chunk_text = join_pages(result["pages"], preserve_inline_spacing=True)
            pages = [
                PageResult(
                    page=page["page"],
                    text=normalize_text(page["text"]),
                    confidence=page.get("confidence"),
                )
                for page in result["pages"]
            ]
            text = join_pages([page.model_dump() for page in pages])
            chunks = (
                [Chunk(**chunk) for chunk in parse_chunks(chunk_text, source=Path(filename).stem)]
                if chunks_mode
                else []
            )
            processing_ms = int((perf_counter() - started) * 1000)

            return ExtractResponse(
                success=True,
                filename=filename,
                mimeType=mime_type,
                extension=extension,
                text=None if chunks_mode else text,
                pages=None if chunks_mode else pages,
                chunks=chunks,
                metadata=ExtractMetadata(
                    ocrUsed=bool(result["metadata"].get("ocrUsed", False)),
                    language=language,
                    characters=len(text),
                    pages=len(pages),
                    processingTimeMs=processing_ms,
                ),
            )
        except Exception as exc:
            if hasattr(exc, "status_code"):
                raise
            raise ExtractionFailedError(f"Extraction failed: {exc}") from exc
        finally:
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def _extractor_for(extension: str):
        extractors = {
            "pdf": PdfExtractor(),
            "txt": TextExtractor(),
            "md": TextExtractor(),
            "numbers": NumbersExtractor(),
            "docx": DocxExtractor(),
            "xlsx": XlsxExtractor(),
            "csv": CsvExtractor(),
            "jpg": ImageExtractor(),
            "jpeg": ImageExtractor(),
            "png": ImageExtractor(),
            "webp": ImageExtractor(),
            "tiff": ImageExtractor(),
        }
        return extractors[extension]
