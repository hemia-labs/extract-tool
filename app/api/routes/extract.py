from typing import Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.extract_response import ExtractResponse
from app.services.extraction_service import ExtractionService
from app.utils.errors import ExtractionError

router = APIRouter(tags=["extract"])

OcrMode = Literal["auto", "true", "false"]
OutputMode = Literal["text", "pages", "markdown"]


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    file: UploadFile = File(...),
    ocr: OcrMode = Form("auto"),
    language: Optional[str] = Form(None),
    output: OutputMode = Form("text"),
) -> ExtractResponse:
    try:
        return await ExtractionService().extract(file, ocr=ocr, language=language, output=output)
    except ExtractionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
