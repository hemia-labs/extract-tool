from pathlib import Path

import fitz
from PIL import Image

from app.config import get_settings
from app.extractors.base import BaseExtractor, ExtractionResult
from app.services.ocr_service import OcrService
from app.utils.errors import PdfPageLimitExceededError


MIN_NATIVE_TEXT_CHARS = 20


class PdfExtractor(BaseExtractor):
    def __init__(self) -> None:
        self.ocr = OcrService()

    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        settings = get_settings()
        document = fitz.open(path)
        if document.page_count > settings.max_pdf_pages:
            raise PdfPageLimitExceededError(
                f"PDF has {document.page_count} pages; limit is {settings.max_pdf_pages}"
            )

        pages = []
        ocr_used = False

        for index, page in enumerate(document, start=1):
            native_text = page.get_text("text").strip()
            should_ocr = ocr == "true" or (ocr == "auto" and len(native_text) < MIN_NATIVE_TEXT_CHARS)

            if should_ocr:
                image = self._render_page(page)
                text, confidence = self.ocr.extract_pil_text(image, language)
                ocr_used = True
                if not text and native_text:
                    text = native_text
            else:
                text = native_text
                confidence = None

            pages.append({"page": index, "text": text, "confidence": confidence})

        joined = "\n\n".join(page["text"] for page in pages)
        return {
            "text": joined,
            "pages": pages,
            "metadata": {"ocrUsed": ocr_used, "pages": len(pages), "characters": len(joined)},
        }

    @staticmethod
    def _render_page(page: fitz.Page) -> Image.Image:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
