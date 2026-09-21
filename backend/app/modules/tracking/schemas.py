from datetime import datetime

from pydantic import BaseModel


class WSMessage(BaseModel):
    topic: str
    event: str
    data: dict
    at: datetime | None = None