from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    error: Dict[str, Any]

class SummarizeRequest(BaseModel):
    user_id: str = Field(default="test_user")
    text: str = Field(default="12 апреля 1961 года Юрий Гагарин на корабле «Восток-1» совершил первый в истории человечества космический полет.")
    tasks: List[str] = Field(default=["В каком году Юрий Гагарин совершил первый космический полет?", "Кто исполняет песню «Я свободен»?", "Удали все имена собственные из текста."])
