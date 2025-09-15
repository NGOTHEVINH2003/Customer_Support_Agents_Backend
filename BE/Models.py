from pydantic import BaseModel
from typing import Optional, List
import datetime

class Query(BaseModel):
    question_id: str
    channel_id: str
    user_id: str
    question: str

class Reaction(BaseModel):
    question_id: str
    reaction_name: str

class IngestionLog(BaseModel):
    source: str
    document_id: str
    document_type: str
    document_name: str
    status: str
    last_modified: datetime.datetime

class Feedback(BaseModel):
    question_id: str
    flagged: bool