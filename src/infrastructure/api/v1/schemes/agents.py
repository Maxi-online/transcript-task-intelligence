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
    text: str = Field(default='On 12 April 1961, Yuri Gagarin made the first space flight in the history of mankind on the East-1 ship.')
    tasks: List[str] = Field(default=['What year did Yuri Gagarin make his first space flight?', 'Who sings "I\'m Free"?', 'Delete all names from the text.'])
