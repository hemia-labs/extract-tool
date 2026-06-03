from pathlib import Path

import chardet

from app.extractors.base import BaseExtractor, ExtractionResult


class TextExtractor(BaseExtractor):
    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding") or "utf-8"
        text = raw.decode(encoding, errors="replace")
        return {
            "text": text,
            "pages": [{"page": 1, "text": text, "confidence": None}],
            "metadata": {"ocrUsed": False, "pages": 1, "characters": len(text)},
        }
