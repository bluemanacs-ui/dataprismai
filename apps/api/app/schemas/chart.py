from pydantic import BaseModel
from typing import Any, Dict, List


class ChartSeries(BaseModel):
    key: str
    label: str


class ChartConfig(BaseModel):
    chart_type: str
    x_key: str
    series: List[ChartSeries]
    title: str
    description: str
    data: List[Dict[str, Any]]
