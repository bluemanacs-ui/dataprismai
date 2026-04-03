from fastapi import APIRouter
from app.skills.catalog import SKILL_CATALOG
from app.schemas.skills import SkillCatalogResponse

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/catalog", response_model=SkillCatalogResponse)
def get_skill_catalog() -> SkillCatalogResponse:
    return SkillCatalogResponse(skills=SKILL_CATALOG)
