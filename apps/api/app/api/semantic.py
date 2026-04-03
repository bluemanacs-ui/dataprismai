from fastapi import APIRouter
from app.semantic.catalog import SEMANTIC_CATALOG
from app.schemas.semantic import SemanticCatalogResponse

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.get("/catalog", response_model=SemanticCatalogResponse)
def get_semantic_catalog() -> SemanticCatalogResponse:
    return SemanticCatalogResponse(
        metrics=SEMANTIC_CATALOG["metrics"],
        dimensions=SEMANTIC_CATALOG["dimensions"],
    )
