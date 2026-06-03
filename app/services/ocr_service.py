from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageOps

from app.config import get_settings
from app.utils.errors import OcrFailedError


class OcrService:
    def extract_image_text(self, path: Path, language: str) -> tuple[str, Optional[float]]:
        try:
            with Image.open(path) as image:
                self._validate_image(image)
                prepared = self._prepare_image(image)
                data = pytesseract.image_to_data(
                    prepared,
                    lang=language,
                    output_type=pytesseract.Output.DICT,
                )
        except Exception as exc:
            raise OcrFailedError(f"OCR failed: {exc}") from exc

        words = [word for word in data["text"] if word.strip()]
        confidences = [
            float(conf)
            for conf in data["conf"]
            if conf not in ("-1", -1) and str(conf).strip()
        ]
        confidence = sum(confidences) / len(confidences) if confidences else None
        return " ".join(words), confidence

    def extract_pil_text(self, image: Image.Image, language: str) -> tuple[str, Optional[float]]:
        try:
            self._validate_image(image)
            prepared = self._prepare_image(image)
            data = pytesseract.image_to_data(
                prepared,
                lang=language,
                output_type=pytesseract.Output.DICT,
            )
        except Exception as exc:
            raise OcrFailedError(f"OCR failed: {exc}") from exc

        words = [word for word in data["text"] if word.strip()]
        confidences = [
            float(conf)
            for conf in data["conf"]
            if conf not in ("-1", -1) and str(conf).strip()
        ]
        confidence = sum(confidences) / len(confidences) if confidences else None
        return " ".join(words), confidence

    def _validate_image(self, image: Image.Image) -> None:
        settings = get_settings()
        if image.width * image.height > settings.max_image_pixels:
            raise OcrFailedError(f"Image exceeds {settings.max_image_pixels} pixel limit")

    @staticmethod
    def _prepare_image(image: Image.Image) -> Image.Image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        return image
