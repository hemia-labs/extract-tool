from typing import Optional

from pydantic import BaseModel, ConfigDict


class QuickAction(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    value: Optional[str] = None


class Chunk(BaseModel):
    id: str
    slug: str
    title: str
    question: Optional[str] = None
    answer: str = ""
    actions: list[QuickAction] = []
