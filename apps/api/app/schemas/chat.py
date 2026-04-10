from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: str = Field(default="analyst")
    workspace: str = Field(default="default")
    workspace_id: str = Field(default="default")
    thread_id: Optional[str] = None
    user_id: str = Field(default="anonymous")
    # Time range filter: L7D, L1M, LQ, L1Y, ALL  (default ALL = no filter)
    time_range: str = Field(default="ALL")
    # Chat mode: pattern | llm | hybrid (default hybrid)
    chat_mode: str = Field(default="hybrid")


class ChatQueryResponse(BaseModel):
    answer: str
    thread_id: Optional[str] = None
    report_id: Optional[str] = None
    # Intent classification fields
    intent_type: str = Field(default="metric_query")
    response_mode: str = Field(default="metric")    # table | schema | metric | insight
    literal_table_name: str = Field(default="")     # explicit table name from user message
    insights: List[str]
    bottlenecks: List[str] = Field(default_factory=list)
    highlight_actions: List[str] = Field(default_factory=list)
    kpi_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    insight_recommendations: List[str]
    follow_ups: List[str]
    assumptions: List[str]
    actions: List[str]
    chart_title: str
    chart_type: str
    chart_config: Dict[str, Any]
    chart_recommendations: List[Dict[str, Any]]
    visualization_config: Optional[Dict[str, Any]] = None
    visualization_recommendations: Optional[List[Dict[str, Any]]] = None
    sql: str
    sql_explanation: str
    sql_validation_issues: List[str]
    result_columns: List[str]
    result_rows: List[Dict[str, Any]]
    result_row_count: int
    result_engine: str
    result_execution_time_ms: int
    semantic_context: dict
    reasoning_steps: List[str] = Field(default_factory=list)
    sql_llm_used: bool = False
    answer_llm_used: bool = False
    model_used: Optional[str] = None
    raw_model_output: Optional[str] = None
    chat_mode: str = Field(default="hybrid")   # pattern | llm | hybrid
