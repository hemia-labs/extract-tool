import csv
from io import StringIO
from pathlib import Path

import chardet

from app.extractors.base import BaseExtractor, ExtractionResult


class CsvExtractor(BaseExtractor):
    def extract(self, path: Path, ocr: str, language: str, output: str) -> ExtractionResult:
        raw = path.read_bytes()
        encoding = chardet.detect(raw).get("encoding") or "utf-8"
        content = raw.decode(encoding, errors="replace")
        sample = content[:4096]
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        rows = list(csv.reader(StringIO(content), dialect))
        text = self._to_markdown(rows) if output == "markdown" else self._to_text(rows)
        return {
            "text": text,
            "pages": [{"page": 1, "text": text, "confidence": None}],
            "metadata": {"ocrUsed": False, "pages": 1, "characters": len(text)},
        }

    @staticmethod
    def _to_text(rows: list[list[str]]) -> str:
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)

    @staticmethod
    def _to_markdown(rows: list[list[str]]) -> str:
        if not rows:
            return ""
        width = max(len(row) for row in rows)
        padded = [row + [""] * (width - len(row)) for row in rows]
        header = "| " + " | ".join(padded[0]) + " |"
        sep = "| " + " | ".join("---" for _ in range(width)) + " |"
        body = ["| " + " | ".join(row) + " |" for row in padded[1:]]
        return "\n".join([header, sep, *body])
