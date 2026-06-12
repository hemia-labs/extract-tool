from typing import Optional

from pydantic import BaseModel

from app.schemas.chunk import Chunk
from app.schemas.page_result import PageResult


class ExtractMetadata(BaseModel):
    ocrUsed: bool
    language: str
    characters: int
    pages: int
    processingTimeMs: int


class ExtractResponse(BaseModel):
    success: bool
    filename: str
    mimeType: str
    extension: str
    text: Optional[str] = None
    pages: Optional[list[PageResult]] = None
    chunks: list[Chunk] = []
    metadata: ExtractMetadata
