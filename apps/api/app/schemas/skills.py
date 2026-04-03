from pydantic import BaseModel
from typing import List


class SkillItem(BaseModel):
    name: str
    title: str
    version: str
    status: str
    owner: str
    description: str
    scope: List[str]
    guardrails: List[str]


class SkillCatalogResponse(BaseModel):
    skills: List[SkillItem]
