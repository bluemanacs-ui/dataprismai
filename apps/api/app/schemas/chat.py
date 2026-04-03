from pydantic import BaseModel, Field
from typing import List


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: str = Field(default="analyst")
    workspace: str = Field(default="default")


class ChatQueryResponse(BaseModel):
    answer: str
    actions: List[str]
    follow_ups: List[str]
    chart_title: str
    chart_type: str
    sql: str
    insights: List[str]
    semantic_context: dict
