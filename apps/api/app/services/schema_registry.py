"""
SchemaRegistry — live, auto-refreshing StarRocks schema discovery.

Reads every table in cc_analytics at startup and keeps a cached registry of:
  - all table names and their columns
  - categorized buckets: semantic / raw / ddm / dp / audit / mapping / other
  - join hints derived from shared key columns across tables
  - a full SCHEMA_CONTEXT string for the SQL prompt
  - a regex that matches any known table name in user messages

Tables are re-categorised automatically as new ones appear — no code changes needed.

Table category rules (applied in order):
  semantic_* → "semantic"   — aggregated analytics views
  dp_*        → "dp"        — data products (analytical outputs)
  ddm_*       → "ddm"       — domain data model (conformed layer)
  raw_*       → "raw"       — raw source tables
  audit_*     → "audit"     — observability / lineage / quality
  *_mapping   → "mapping"   — reference / crosswalk tables
  everything else → "other"
"""

from __future__ import annotations

import logging
import re
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

# Priority ordering for table categories (higher = more preferred for analytics)
_CATEGORY_PRIORITY = {
    "semantic": 10,
    "dp": 8,
    "ddm": 6,
    "raw": 4,
    "audit": 2,
    "mapping": 1,
    "other": 0,
}

# Category → human-readable label for prompt section headers
_CATEGORY_LABEL = {
    "semantic": "Semantic Tables (pre-aggregated analytics — PREFER for analytics queries)",
    "dp": "Data Product Tables (analytical outputs — use when semantic tables lack detail)",
    "ddm": "Domain Data Model Tables (conformed / enriched — use for joins and drill-downs)",
    "raw": "Raw Source Tables (event-level — use only for specific lookups)",
    "audit": "Audit Tables (pipeline runs, quality checks — use for operational queries)",
    "mapping": "Mapping / Reference Tables (lookups, crosswalks)",
    "other": "Other Tables",
}

# Well-known join key column names — used to infer join hints automatically
_JOIN_KEY_COLS = frozenset(
    {
        "customer_id", "account_id", "transaction_id",
        "merchant_id", "card_id", "payment_id", "statement_id",
        "country_code", "legal_entity", "kpi_month", "spend_month",
        "metric_date", "as_of_date", "reporting_month",
    }
)


def _categorise(table_name: str) -> str:
    n = table_name.lower()
    # Check suffix patterns before prefix patterns so that tables like
    # semantic_metric_mapping are classified as "mapping", not "semantic".
    if n.endswith("_mapping"):
        return "mapping"
    if n.endswith("_ddm"):
        return "ddm"
    if n.startswith("semantic_"):
        return "semantic"
    if n.startswith("dp_"):
        return "dp"
    if n.startswith("ddm_"):
        return "ddm"
    if n.startswith("raw_"):
        return "raw"
    if n.startswith("audit_"):
        return "audit"
    return "other"


# ---------------------------------------------------------------------------
# SchemaRegistry
# ---------------------------------------------------------------------------
class SchemaRegistry:
    """Thread-safe, lazily-loaded StarRocks schema registry.

    Call `registry.refresh()` to reload from DB.
    All properties are safe to read from any thread; they return stale data while
    a refresh is in progress.
    """

    _REFRESH_INTERVAL_SECS = 300  # 5 minutes background poll

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tables: dict[str, dict[str, Any]] = {}   # table_name → {cols, category, qualified}
        self._loaded = False
        self._last_failed_at: float = 0.0   # monotonic timestamp of last refresh failure
        self._background_thread: threading.Thread | None = None

    # Minimum seconds between back-to-back refresh retries after a failure
    _RETRY_THROTTLE_SECS = 30

    # ── Internal helpers ────────────────────────────────────────────────────

    def _get_conn(self):
        import mysql.connector
        from app.core.config import settings
        return mysql.connector.connect(
            host=settings.starrocks_host,
            port=settings.starrocks_port,
            user=settings.starrocks_user,
            password=settings.starrocks_password,
            database=settings.starrocks_database,
            connection_timeout=5,
        )

    def _fetch_all(self) -> dict[str, dict[str, Any]]:
        conn = self._get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute("SHOW TABLES FROM cc_analytics")
        table_names = [list(r.values())[0] for r in cur.fetchall()]
        result: dict[str, dict[str, Any]] = {}
        for tname in table_names:
            category = _categorise(tname)
            try:
                cur.execute(f"DESCRIBE cc_analytics.`{tname}`")
                cols = [r["Field"] for r in cur.fetchall()]
            except Exception:
                cols = []
            # Infer time column (first date/datetime-ish column)
            time_col = next(
                (c for c in cols if c in (
                    "transaction_date", "metric_date", "as_of_date", "kpi_month",
                    "spend_month", "signal_date", "statement_date", "payment_date",
                    "profile_date", "run_date", "snapshot_month", "log_date",
                )),
                None,
            )
            result[tname] = {
                "category": category,
                "columns": cols,
                "qualified": f"cc_analytics.{tname}",
                "time_col": time_col,
            }
        conn.close()
        logger.info(
            "SchemaRegistry loaded %d tables (%d categories)",
            len(result),
            len({v["category"] for v in result.values()}),
        )
        return result

    # ── Public refresh ───────────────────────────────────────────────────────

    def refresh(self) -> None:
        try:
            tables = self._fetch_all()
            with self._lock:
                self._tables = tables
                self._loaded = True
                self._last_failed_at = 0.0   # clear failure marker on success
        except Exception as exc:
            logger.warning("SchemaRegistry refresh failed: %s", exc)
            with self._lock:
                # Do NOT set _loaded=True — allow the next ensure_loaded() to retry
                # (subject to the retry throttle).
                self._last_failed_at = time.monotonic()

    def ensure_loaded(self) -> None:
        with self._lock:
            if self._loaded and self._tables:
                return  # loaded with data — fast return
            # Throttle retries after a failure: don't hammer StarRocks on every request
            if self._last_failed_at and (time.monotonic() - self._last_failed_at) < self._RETRY_THROTTLE_SECS:
                return  # too soon to retry — use whatever _tables we have (may be empty)
        # First load OR throttle window has passed — attempt (re)load synchronously
        self.refresh()
        self._start_background_refresh()

    def _start_background_refresh(self) -> None:
        if self._background_thread and self._background_thread.is_alive():
            return

        def _loop():
            while True:
                time.sleep(self._REFRESH_INTERVAL_SECS)
                self.refresh()

        t = threading.Thread(target=_loop, daemon=True, name="schema-registry-refresh")
        t.start()
        self._background_thread = t

    # ── Accessors ────────────────────────────────────────────────────────────

    def _tables_snapshot(self) -> dict[str, dict[str, Any]]:
        self.ensure_loaded()
        with self._lock:
            return dict(self._tables)

    def all_tables(self) -> dict[str, dict[str, Any]]:
        """Return {table_name: metadata} for all queryable tables."""
        return self._tables_snapshot()

    def tables_by_category(self, category: str) -> dict[str, dict[str, Any]]:
        return {k: v for k, v in self._tables_snapshot().items() if v["category"] == category}

    def get_table(self, name: str) -> dict[str, Any] | None:
        return self._tables_snapshot().get(name)

    def known_table_names(self) -> frozenset[str]:
        return frozenset(self._tables_snapshot().keys())

    def qualified_name(self, table: str) -> str | None:
        t = self._tables_snapshot().get(table)
        return t["qualified"] if t else None

    def columns_for(self, table: str) -> list[str]:
        t = self._tables_snapshot().get(table)
        return t["columns"] if t else []

    # ── Observability ────────────────────────────────────────────────────────

    def log_table_lookup(
        self,
        table_name: str,
        found: bool,
        *,
        category: str | None = None,
        sql: str | None = None,
        response_mode: str | None = None,
        suggestions: list[str] | None = None,
    ) -> None:
        """Log a table lookup for observability — call from every literal-table code path."""
        if found:
            logger.info(
                "SchemaRegistry lookup: '%s' FOUND | category=%s | response_mode=%s | sql_preview=%.120s",
                table_name,
                category or "?",
                response_mode or "?",
                (sql or "").splitlines()[0] if sql else "",
            )
        else:
            logger.warning(
                "SchemaRegistry lookup: '%s' NOT FOUND | registry_size=%d | suggestions=%s",
                table_name,
                len(self._tables_snapshot()),
                suggestions or [],
            )

    # ── Table name regex (for message scanning) ──────────────────────────────

    def table_name_regex(self) -> re.Pattern:
        """Return a compiled regex matching any known table name in user messages."""
        names = sorted(self.known_table_names(), key=len, reverse=True)  # longest first
        if not names:
            return re.compile(r"(?!)")  # never matches
        pattern = r"\b(" + "|".join(re.escape(n) for n in names) + r")\b"
        return re.compile(pattern, re.IGNORECASE)

    # ── Join hints ───────────────────────────────────────────────────────────

    def infer_join_hints(self) -> list[str]:
        """Return a list of 'tableA.col → tableB.col' strings for common join keys."""
        snapshot = self._tables_snapshot()
        # Build {col → [table, ...]} index
        col_to_tables: dict[str, list[str]] = {}
        for tname, meta in snapshot.items():
            for col in meta["columns"]:
                if col in _JOIN_KEY_COLS:
                    col_to_tables.setdefault(col, []).append(tname)

        hints: list[str] = []
        seen: set[frozenset] = set()
        for col, tables in sorted(col_to_tables.items()):
            # Prioritise links involving semantic/dp tables
            tables_sorted = sorted(
                tables,
                key=lambda t: -_CATEGORY_PRIORITY.get(snapshot[t]["category"], 0),
            )
            for i, a in enumerate(tables_sorted):
                for b in tables_sorted[i + 1 :]:
                    pair = frozenset({a, b})
                    if pair not in seen:
                        hints.append(f"{a}.{col}  →  {b}.{col}")
                        seen.add(pair)
        return hints[:60]  # cap to keep prompt manageable

    # ── SCHEMA_CONTEXT string ────────────────────────────────────────────────

    def build_schema_context(self) -> str:
        snapshot = self._tables_snapshot()
        lines: list[str] = [
            "Database: cc_analytics (StarRocks / MySQL-compatible)",
            "Countries: SG (Singapore / SGD), MY (Malaysia / MYR), IN (India / INR)",
            "",
        ]

        # Emit sections in priority order (most preferred first)
        for category in ("semantic", "dp", "ddm", "raw", "audit", "mapping", "other"):
            tables = {k: v for k, v in snapshot.items() if v["category"] == category}
            if not tables:
                continue
            lines.append(f"=== {_CATEGORY_LABEL[category]} ===")
            for tname in sorted(tables):
                cols = tables[tname]["columns"]
                # Chunk columns into groups of 8 to keep lines readable
                chunks = [cols[i : i + 8] for i in range(0, len(cols), 8)]
                first = True
                for chunk in chunks:
                    prefix = f"{tname}(" if first else "    "
                    suffix = (", " if chunk != chunks[-1] else ")") if first else (", " if chunk != chunks[-1] else "")
                    if first:
                        lines.append(f"{tname}({', '.join(chunk)}" + ("," if len(chunks) > 1 else ")"))
                        first = False
                    else:
                        lines.append(f"  {', '.join(chunk)}" + ("," if chunk != chunks[-1] else ")")
                )
            lines.append("")

        # Join hints
        hints = self.infer_join_hints()
        if hints:
            lines.append("=== Join Keys ===")
            lines.extend(hints)
            lines.append("")

        lines += [
            "=== Important Query Rules ===",
            "- Always prefix table names with cc_analytics. (e.g. cc_analytics.semantic_customer_360)",
            "- PREFER semantic_* tables for aggregated analytics; use dp_* when you need richer column coverage",
            "- Use DATE_FORMAT(col, '%Y-%m') for monthly grouping; do NOT use date_trunc",
            "- Data covers 2025 (full year Jan–Dec 2025); all semantic tables span 2025-01 to 2025-12",
            "- customer_segment values (lowercase): mass, affluent, premium",
            "- payment_status values: paid_full, paid_partial, paid_minimum, overdue, pending",
            "- auth_status values: approved, declined",
            "- transaction_type values: purchase, declined",
            "- overdue_bucket values: current, '1-30 days', '31-60 days'",
            "- channel values: online, pos, contactless, mobile, atm",
            "- legal_entity values: SG_BANK, MY_BANK, IN_BANK",
            "- risk_rating values: low, medium, high",
            "- kyc_status values: verified, pending, enhanced_dd",
            "- credit_band values: poor, fair, good, very_good, excellent",
            "- merchant_risk_tier values: low, medium",
            "- fraud_score > 0.6 = suspicious; > 0.85 = high risk; is_suspicious=1 for flagged",
            "- Country code mapping: Malaysia='MY', Singapore='SG', India='IN'",
            "- For customer name lookups: WHERE full_name LIKE '%Name%' or WHERE first_name='Name'",
            "- For top-N spend: use cc_analytics.semantic_spend_metrics ORDER BY total_spend DESC",
            "- For spend by category: use pre-aggregated columns in semantic_spend_metrics (food_dining, retail_shopping, travel_transport, grocery, entertainment, utilities, healthcare, hotel, fuel, other_spend)",
            "- semantic_portfolio_kpis is best for executive-level KPIs (rates stored as decimals — multiply by 100 for %)",
            "- utilization_pct and avg_utilization are decimals (0–1) — multiply by 100 for %",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
registry = SchemaRegistry()
