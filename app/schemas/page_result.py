from typing import Optional

from pydantic import BaseModel


class PageResult(BaseModel):
    page: int
    text: str
    confidence: Optional[float] = None
