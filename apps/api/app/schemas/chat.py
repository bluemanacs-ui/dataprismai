from pydantic import BaseModel, Field
from typing import List, Optional


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: str = Field(default="analyst")
    workspace: str = Field(default="default")


class ChatQueryResponse(BaseModel):
    answer: str
    insights: List[str]
    follow_ups: List[str]
    assumptions: List[str]
    actions: List[str]
    chart_title: str
    chart_type: str
    sql: str
    sql_explanation: str
    sql_validation_issues: List[str]
    semantic_context: dict
    raw_model_output: Optional[str] = None
