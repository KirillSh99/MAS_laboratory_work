from pydantic import BaseModel
from typing import List

class UserRequest(BaseModel):
    prompt: str

class AgentResponse(BaseModel):
    draft: str
    edited_text: str
    critic_score: int
    critic_feedback: str
    logs: List[str]

    class Config:
        from_attributes = True