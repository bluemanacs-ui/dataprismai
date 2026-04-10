"""
query_executor_service.py
─────────────────────────
Single-engine execution layer: StarRocks via MySQL wire protocol.
Uses a module-level connection pool for low-latency repeated queries.
Every executed query is written to the StarRocks query_audit_log table
for observability.
"""
import time
import random
import logging
from decimal import Decimal
from datetime import datetime, date

import mysql.connector
import mysql.connector.pooling

from app.schemas.execution import QueryExecutionResult
from app.services.config_service import config_svc

logger = logging.getLogger(__name__)

_POOL: mysql.connector.pooling.MySQLConnectionPool | None = None
_POOL_CONFIG_SNAPSHOT: dict = {}


def _sr_config() -> dict:
    return {
        "host":               config_svc.get("starrocks.host",     "localhost"),
        "port":               config_svc.get_int("starrocks.port", 9030),
        "user":               config_svc.get("starrocks.user",     "root"),
        "password":           config_svc.get("starrocks.password", ""),
        "database":           config_svc.get("starrocks.database", "cc_analytics"),
        "connection_timeout": config_svc.get_int("starrocks.query_timeout", 30),
        "autocommit": True,
    }


def _get_pool() -> mysql.connector.pooling.MySQLConnectionPool:
    global _POOL, _POOL_CONFIG_SNAPSHOT
    cfg = _sr_config()
    if _POOL is None or cfg != _POOL_CONFIG_SNAPSHOT:
        _POOL = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="sr_pool",
            pool_size=config_svc.get_int("starrocks.pool_size", 20),
            pool_reset_session=True,
            **cfg,
        )
        _POOL_CONFIG_SNAPSHOT = cfg
    return _POOL


def _serialise_row(row: dict) -> dict:
    """Convert Decimal / date / datetime to JSON-friendly types."""
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, (datetime, date)):
            out[k] = str(v)
        else:
            out[k] = v
    return out


def execute_query(engine: str, sql: str, semantic_context: dict) -> QueryExecutionResult:
    """Execute *sql* against StarRocks and return a QueryExecutionResult."""
    start_ts = time.time()
    status   = "success"
    error_msg: str | None = None
    columns: list[str] = []
    rows: list[dict] = []

    try:
        # Retry up to 3 times on pool-exhausted errors with brief back-off
        conn = None
        for attempt in range(3):
            try:
                conn = _get_pool().get_connection()
                break
            except Exception as pool_exc:
                if "pool exhausted" in str(pool_exc).lower() and attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
                else:
                    raise
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        raw_rows = cursor.fetchall()
        columns  = [d[0] for d in (cursor.description or [])]
        rows     = [_serialise_row(dict(r)) for r in raw_rows]
        cursor.close()
        conn.close()
    except Exception as exc:
        status    = "error"
        error_msg = str(exc)
        logger.warning("StarRocks query error: %s", exc)

    exec_ms = int((time.time() - start_ts) * 1000)

    # Fire-and-forget audit log (non-blocking; failure doesn't raise)
    _write_audit_log(
        thread_id=semantic_context.get("thread_id") or "",
        user_id=semantic_context.get("user_id") or "",
        persona=semantic_context.get("persona") or "",
        country_code=semantic_context.get("country_code") or "",
        user_message=semantic_context.get("metric") or "",
        generated_sql=sql,
        engine="StarRocks",
        row_count=len(rows),
        execution_time_ms=exec_ms,
        status=status,
        error_message=error_msg or "",
    )

    if status == "error":
        raise RuntimeError(error_msg)

    return QueryExecutionResult(
        engine="StarRocks",
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=exec_ms,
        status="success",
    )


def _write_audit_log(**fields) -> None:
    try:
        conn   = _get_pool().get_connection()
        cursor = conn.cursor()
        import uuid as _uuid
        log_id = str(_uuid.uuid4())
        cursor.execute(
            "INSERT INTO cc_analytics.audit_query_log "
            "(log_id, log_date, user_id, persona, country_code, message, sql_generated, "
            " tables_accessed, row_count, latency_ms, success, error_message, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                log_id,
                datetime.utcnow().date(),
                fields.get("user_id", "")[:30],
                fields.get("persona", "")[:50],
                fields.get("country_code", "")[:5],
                fields.get("user_message", "")[:1000],
                fields.get("generated_sql", "")[:4000],
                "",  # tables_accessed — could parse from SQL if needed
                fields.get("row_count", 0),
                fields.get("execution_time_ms", 0),
                1 if fields.get("status", "success") == "success" else 0,
                fields.get("error_message", "")[:500],
                datetime.utcnow(),
            ),
        )
        cursor.close()
        conn.close()
    except Exception:
        pass  # audit failure must never break the main query path
