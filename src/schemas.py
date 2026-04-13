from pydantic import BaseModel
from typing import List, Optional


class Task(BaseModel):
    intent: str                  # create_file | write_code | summarize | chat
    parameters: dict
    confidence: float


class AgentResponse(BaseModel):
    tasks: List[Task]
    raw_text: Optional[str] = None


class ActionResult(BaseModel):
    intent: str
    success: bool
    message: str
    output: Optional[str] = None