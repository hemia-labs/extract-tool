from typing import Optional, Union

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
    agent: Optional[str] = None
    intent: Optional[str] = None
    # A string is a reference to a catalog action id; an object is an inline
    # action definition.
    actions: list[Union[str, QuickAction]] = []
