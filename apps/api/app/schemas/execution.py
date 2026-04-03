from pydantic import BaseModel
from typing import Any, Dict, List


class QueryExecutionResult(BaseModel):
    engine: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: int
    status: str
