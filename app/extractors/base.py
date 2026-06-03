from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


ExtractionResult = dict[str, Any]


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        raise NotImplementedError
