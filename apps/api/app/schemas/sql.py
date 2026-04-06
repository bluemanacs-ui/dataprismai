from pydantic import BaseModel
from typing import List


class SQLGenerationResult(BaseModel):
    sql: str
    explanation: str
    assumptions: List[str]
    llm_was_used: bool = False
