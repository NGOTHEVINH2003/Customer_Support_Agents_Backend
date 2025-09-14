from pydantic import BaseModel
from typing import Optional, List

class Query(BaseModel):
    question_id: str
    question: str
    answer: str
    similarity_score: float

class IngestionLog(BaseModel):
    source: str
    document_id: str
    status: str
    metadata: Optional[str] = None
    last_modified: Optional[str] = None

class Feedback(BaseModel):
    question_id: str
    flagged: bool
    ThumbsUp: Optional[bool] = None
    ThumbsDown: Optional[bool] = None