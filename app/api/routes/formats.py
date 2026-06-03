from fastapi import APIRouter

from app.services.mime_detector import SUPPORTED_EXTENSIONS

router = APIRouter(tags=["formats"])


@router.get("/formats")
async def formats() -> dict[str, list[str]]:
    return {"formats": sorted(SUPPORTED_EXTENSIONS)}
