from pathlib import Path

from app.extractors.base import BaseExtractor, ExtractionResult
from app.services.ocr_service import OcrService


class ImageExtractor(BaseExtractor):
    def __init__(self) -> None:
        self.ocr = OcrService()

    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        text, confidence = self.ocr.extract_image_text(path, language)
        return {
            "text": text,
            "pages": [{"page": 1, "text": text, "confidence": confidence}],
            "metadata": {"ocrUsed": True, "pages": 1, "characters": len(text)},
        }
