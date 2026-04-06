from fastapi import APIRouter
from app.semantic.catalog import SEMANTIC_CATALOG
from app.schemas.semantic import SemanticCatalogResponse
from app.core.config import settings

router = APIRouter(prefix="/semantic", tags=["semantic"])


@router.get("/catalog", response_model=SemanticCatalogResponse)
def get_semantic_catalog() -> SemanticCatalogResponse:
    return SemanticCatalogResponse(
        metrics=SEMANTIC_CATALOG["metrics"],
        dimensions=SEMANTIC_CATALOG["dimensions"],
    )


@router.get("/tables")
def get_tables() -> dict:
    """Return StarRocks table metadata for the Data Explorer."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=settings.starrocks_host,
            port=settings.starrocks_port,
            user=settings.starrocks_user,
            password=settings.starrocks_password,
            database=settings.starrocks_database,
            connection_timeout=5,
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")
        raw = cursor.fetchall()
        table_names = [list(row.values())[0] for row in raw]
        tables = []
        for tname in table_names:
            try:
                cursor.execute(f"DESCRIBE `{tname}`")
                cols = [{"name": r.get("Field", ""), "type": r.get("Type", ""), "nullable": r.get("Null", ""), "key": r.get("Key", "")} for r in cursor.fetchall()]
                cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{tname}`")
                row_count = (cursor.fetchone() or {}).get("cnt", 0)
                tables.append({"name": tname, "columns": cols, "row_count": row_count})
            except Exception:
                tables.append({"name": tname, "columns": [], "row_count": 0})
        conn.close()
        return {"tables": tables, "database": settings.starrocks_database}
    except Exception as e:
        return {"tables": [], "database": settings.starrocks_database, "error": str(e)}


@router.get("/sample/{table_name}")
def get_table_sample(table_name: str, limit: int = 10, offset: int = 0) -> dict:
    """Return up to `limit` rows from `offset` for paginated sample data."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=settings.starrocks_host,
            port=settings.starrocks_port,
            user=settings.starrocks_user,
            password=settings.starrocks_password,
            database=settings.starrocks_database,
            connection_timeout=5,
        )
        cursor = conn.cursor(dictionary=True)
        safe_limit = max(1, min(int(limit), 20))
        safe_offset = max(0, int(offset))
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {safe_limit} OFFSET {safe_offset}")
        rows = cursor.fetchall()
        conn.close()
        serialisable = []
        for row in rows:
            serialisable.append({k: (str(v) if v is not None else None) for k, v in row.items()})
        return {"rows": serialisable, "table": table_name, "offset": safe_offset, "limit": safe_limit}
    except Exception as e:
        return {"rows": [], "table": table_name, "offset": 0, "limit": limit, "error": str(e)}


@router.get("/user-context/{user_id}")
def get_user_context(user_id: str) -> dict:
    """Return domain, allowed semantic tables, and access info for a user."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=settings.starrocks_host,
            port=settings.starrocks_port,
            user=settings.starrocks_user,
            password=settings.starrocks_password,
            database=settings.starrocks_database,
            connection_timeout=5,
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT domain, access_level, country_code FROM user_domain_mapping WHERE user_id = %s", (user_id,))
        domain_rows = cursor.fetchall()
        allowed_domains = list({r["domain"] for r in domain_rows})
        conn.close()
        return {"user_id": user_id, "allowed_domains": allowed_domains, "domain_rows": [
            {k: v for k, v in r.items()} for r in domain_rows
        ]}
    except Exception as e:
        return {"user_id": user_id, "allowed_domains": [], "error": str(e)}

