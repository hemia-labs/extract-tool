from pydantic import BaseModel

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
    text: str
    pages: list[PageResult]
    metadata: ExtractMetadata
