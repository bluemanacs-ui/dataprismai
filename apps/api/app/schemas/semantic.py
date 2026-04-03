from pydantic import BaseModel
from typing import List


class SemanticMetric(BaseModel):
    name: str
    keywords: List[str]
    dimensions: List[str]
    engine: str
    domain: str
    definition: str


class SemanticDimension(BaseModel):
    name: str
    keywords: List[str]


class SemanticCatalogResponse(BaseModel):
    metrics: List[SemanticMetric]
    dimensions: List[SemanticDimension]