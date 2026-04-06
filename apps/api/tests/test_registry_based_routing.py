"""Regression tests: SchemaRegistry-backed chatbot routing.

Verifies that ALL tables visible in StarRocks (including semantic_*, *_mapping,
dp_*, ddm_*, audit_*) are treated as valid queryable objects by the chatbot
pipeline — not just raw_* tables.

Run with:  pytest apps/api/tests/ -v -k registry

All tests use unittest.mock to avoid requiring a live StarRocks connection.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Shared registry fixture
# ---------------------------------------------------------------------------

# Mapping and semantic tables that the profiling UI can see but the chatbot
# historically treated as "not found".
_MAPPING_TABLES = {
    "semantic_metric_mapping": {
        "category": "mapping",
        "columns": ["metric_id", "metric_name", "domain", "source_table"],
        "qualified": "cc_analytics.semantic_metric_mapping",
        "time_col": None,
    },
    "domain_semantic_mapping": {
        "category": "mapping",
        "columns": ["domain", "semantic_table", "persona"],
        "qualified": "cc_analytics.domain_semantic_mapping",
        "time_col": None,
    },
    "intent_domain_mapping": {
        "category": "mapping",
        "columns": ["intent_keyword", "domain", "confidence_score"],
        "qualified": "cc_analytics.intent_domain_mapping",
        "time_col": None,
    },
    "user_domain_mapping": {
        "category": "mapping",
        "columns": ["user_id", "domain", "access_level", "country_code"],
        "qualified": "cc_analytics.user_domain_mapping",
        "time_col": None,
    },
    "domain_grain_mapping": {
        "category": "mapping",
        "columns": ["domain", "grain", "source_table"],
        "qualified": "cc_analytics.domain_grain_mapping",
        "time_col": None,
    },
    "semantic_glossary_metrics": {
        "category": "semantic",
        "columns": ["metric_id", "metric_name", "definition", "domain"],
        "qualified": "cc_analytics.semantic_glossary_metrics",
        "time_col": None,
    },
}

_RAW_TABLES = {
    "raw_customer": {
        "category": "raw",
        "columns": ["customer_id", "first_name", "last_name"],
        "qualified": "cc_analytics.raw_customer",
        "time_col": None,
    },
    "raw_transaction": {
        "category": "raw",
        "columns": ["txn_id", "customer_id", "txn_amount"],
        "qualified": "cc_analytics.raw_transaction",
        "time_col": "transaction_date",
    },
}

_ALL_MOCK_TABLES = {**_MAPPING_TABLES, **_RAW_TABLES}


def _mock_registry(tables: dict | None = None):
    """Return a MagicMock that behaves like SchemaRegistry."""
    t = tables if tables is not None else _ALL_MOCK_TABLES
    m = MagicMock()
    m.get_table.side_effect = lambda name: t.get(name)
    m.all_tables.return_value = t
    m.known_table_names.return_value = frozenset(t.keys())
    m.qualified_name.side_effect = lambda name: t[name]["qualified"] if name in t else None
    m.columns_for.side_effect = lambda name: t.get(name, {}).get("columns", [])
    m.log_table_lookup.return_value = None
    import re
    names = sorted(t.keys(), key=len, reverse=True)
    pattern = r"\b(" + "|".join(re.escape(n) for n in names) + r")\b" if names else r"(?!)"
    m.table_name_regex.return_value = re.compile(pattern, re.IGNORECASE)
    return m


# ===========================================================================
# 1. Registry-backed existence checks
# ===========================================================================

class TestRegistryExistenceChecks:
    """Mapping/semantic tables must be recognized as valid by all pipeline nodes."""

    @patch("app.graph_nodes.planner_node._schema_registry")
    def test_semantic_metric_mapping_recognized_by_planner(self, mock_reg):
        mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
        from app.graph_nodes.planner_node import planner_node
        state = planner_node({"user_message": "show row count for semantic_metric_mapping"})
        assert state["literal_table_name"] == "semantic_metric_mapping"

    @patch("app.graph_nodes.planner_node._schema_registry")
    def test_domain_semantic_mapping_recognized_by_planner(self, mock_reg):
        mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
        from app.graph_nodes.planner_node import planner_node
        state = planner_node({"user_message": "show sample data from domain_semantic_mapping"})
        assert state["literal_table_name"] == "domain_semantic_mapping"

    def test_semantic_metric_mapping_found_in_vanna(self):
        """vanna_sql_node must NOT return 'not found' for a registry-known mapping table."""
        mock_reg = _mock_registry()
        with patch("app.graph_nodes.vanna_sql_node._schema_registry", mock_reg):
            from app.graph_nodes.vanna_sql_node import vanna_sql_node
            state = vanna_sql_node({
                "user_message": "show row count for semantic_metric_mapping",
                "intent_type": "preview_data",
                "literal_table_name": "semantic_metric_mapping",
                "persona": "analyst",
                "semantic_context": {},
                "prior_context": [],
            })
        assert "not_found" not in (state.get("generated_sql") or "").lower()
        assert "not found" not in state.get("answer", "").lower()


# ===========================================================================
# 2. Mapping category classification
# ===========================================================================

class TestMappingCategoryClassification:
    """Mapping tables must be classified as 'mapping', not 'semantic'."""

    def test_semantic_metric_mapping_is_mapping_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("semantic_metric_mapping") == "mapping"

    def test_domain_semantic_mapping_is_mapping_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("domain_semantic_mapping") == "mapping"

    def test_intent_domain_mapping_is_mapping_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("intent_domain_mapping") == "mapping"

    def test_user_domain_mapping_is_mapping_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("user_domain_mapping") == "mapping"

    def test_semantic_customer_360_is_semantic_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("semantic_customer_360") == "semantic"

    def test_raw_table_is_raw_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("raw_customer") == "raw"

    def test_dp_table_is_dp_category(self):
        from app.services.schema_registry import _categorise
        assert _categorise("dp_risk_signals") == "dp"


# ===========================================================================
# 3. Preview / count / schema SQL generation for mapping tables
# ===========================================================================

class TestMappingTableSqlGeneration:
    """Deterministic SQL must be generated for mapping table queries."""

    def _run_vanna(self, message: str, table: str, intent: str) -> dict:
        mock_reg = _mock_registry()
        with patch("app.graph_nodes.vanna_sql_node._schema_registry", mock_reg):
            from app.graph_nodes.vanna_sql_node import vanna_sql_node
            return vanna_sql_node({
                "user_message": message,
                "intent_type": intent,
                "literal_table_name": table,
                "persona": "analyst",
                "semantic_context": {},
                "prior_context": [],
            })

    def test_row_count_semantic_metric_mapping(self):
        result = self._run_vanna(
            "show row count for semantic_metric_mapping",
            "semantic_metric_mapping",
            "preview_data",
        )
        sql = result["generated_sql"].upper()
        assert "COUNT(*)" in sql
        assert "SEMANTIC_METRIC_MAPPING" in sql
        assert "NOT_FOUND" not in sql

    def test_sample_domain_semantic_mapping(self):
        result = self._run_vanna(
            "show sample data from domain_semantic_mapping",
            "domain_semantic_mapping",
            "preview_data",
        )
        sql = result["generated_sql"].upper()
        assert "SELECT *" in sql
        assert "DOMAIN_SEMANTIC_MAPPING" in sql
        assert "LIMIT" in sql

    def test_describe_semantic_metric_mapping(self):
        result = self._run_vanna(
            "describe semantic_metric_mapping",
            "semantic_metric_mapping",
            "schema_query",
        )
        sql = result["generated_sql"].upper()
        assert "INFORMATION_SCHEMA" in sql
        assert "SEMANTIC_METRIC_MAPPING" in sql

    def test_response_mode_is_table_for_preview(self):
        """vanna_sql_node does not set response_mode but planner must."""
        from app.graph_nodes.planner_node import planner_node
        with patch("app.graph_nodes.planner_node._schema_registry") as mock_reg:
            mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
            state = planner_node({"user_message": "show sample data from domain_semantic_mapping"})
        assert state["response_mode"] == "table"

    def test_response_mode_is_schema_for_describe(self):
        from app.graph_nodes.planner_node import planner_node
        with patch("app.graph_nodes.planner_node._schema_registry") as mock_reg:
            mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
            state = planner_node({"user_message": "describe semantic_metric_mapping"})
        assert state["response_mode"] == "schema"

    def test_query_targets_starrocks_qualified_name(self):
        """Generated SQL must include the fully-qualified StarRocks table name."""
        result = self._run_vanna(
            "show row count for semantic_metric_mapping",
            "semantic_metric_mapping",
            "preview_data",
        )
        assert "cc_analytics.semantic_metric_mapping" in result["generated_sql"].lower()


# ===========================================================================
# 4. Not-found behavior — suggestions from full registry
# ===========================================================================

class TestNotFoundBehavior:
    """When a table truly doesn't exist, suggestions must come from the full registry."""

    def _run_vanna_unknown(self, message: str, table: str) -> dict:
        mock_reg = _mock_registry()
        with patch("app.graph_nodes.vanna_sql_node._schema_registry", mock_reg), \
             patch("app.services.sql_generation_service._schema_registry", mock_reg):
            from app.graph_nodes.vanna_sql_node import vanna_sql_node
            return vanna_sql_node({
                "user_message": message,
                "intent_type": "preview_data",
                "literal_table_name": table,
                "persona": "analyst",
                "semantic_context": {},
                "prior_context": [],
            })

    def test_truly_nonexistent_table_returns_not_found(self):
        result = self._run_vanna_unknown(
            "show data from nonexistent_table_xyz",
            "nonexistent_table_xyz",
        )
        answer = result.get("answer", "")
        assert "not found" in answer.lower() or "generated_sql" not in result or not result.get("generated_sql")

    def test_not_found_answer_mentions_available_tables(self):
        result = self._run_vanna_unknown(
            "show from totally_fake_table",
            "totally_fake_table",
        )
        answer = result.get("answer", "")
        # Must mention at least one real table category from the registry
        assert any(cat in answer.lower() for cat in ("mapping", "raw", "semantic", "dp", "ddm"))

    def test_suggestions_include_mapping_tables(self):
        """Not-found suggestions must include mapping tables, not only raw_*."""
        result = self._run_vanna_unknown(
            "show data from semantic_metric_mappping",  # typo — one extra p
            "semantic_metric_mappping",
        )
        answer = result.get("answer", "")
        # The registry knows semantic_metric_mapping — it should appear as a suggestion
        assert "semantic_metric_mapping" in answer or "mapping" in answer.lower()

    def test_not_found_does_not_only_suggest_raw_tables(self):
        """Suggestions must not be limited to raw_* — full registry must be presented."""
        result = self._run_vanna_unknown(
            "describe frobnitz_table",
            "frobnitz_table",
        )
        answer = result.get("answer", "")
        # At least one non-raw category from our mock should appear
        non_raw_keys = [k for k in _ALL_MOCK_TABLES if not k.startswith("raw_")]
        assert any(k in answer for k in non_raw_keys) or "mapping" in answer.lower()


# ===========================================================================
# 5. SchemaRegistry retry behavior (unit tests — no live DB)
# ===========================================================================

class TestSchemaRegistryRetry:
    """ensure_loaded must retry after a failure once the throttle window passes."""

    def test_failed_load_does_not_permanently_lock_registry(self):
        from app.services.schema_registry import SchemaRegistry
        reg = SchemaRegistry()

        call_count = [0]
        def failing_fetch():
            call_count[0] += 1
            raise ConnectionError("StarRocks not ready")

        reg._fetch_all = failing_fetch
        reg.ensure_loaded()  # first call — fails, records failure time
        assert not reg._loaded
        assert reg._last_failed_at > 0

        # Simulate throttle window passing by backdating the failure timestamp
        import time
        reg._last_failed_at = time.monotonic() - reg._RETRY_THROTTLE_SECS - 1

        reg.ensure_loaded()  # second call after throttle — should retry
        assert call_count[0] == 2, "Should have retried after throttle window"

    def test_successful_load_clears_failure_marker(self):
        from app.services.schema_registry import SchemaRegistry
        reg = SchemaRegistry()

        def success_fetch():
            return {"raw_customer": {"category": "raw", "columns": [], "qualified": "cc_analytics.raw_customer", "time_col": None}}

        reg._fetch_all = success_fetch
        reg.ensure_loaded()
        assert reg._loaded
        assert reg._last_failed_at == 0.0
        assert reg.get_table("raw_customer") is not None

    def test_registry_populated_after_recovery(self):
        """After initial failure + throttle window, a successful retry populates tables."""
        from app.services.schema_registry import SchemaRegistry
        import time
        reg = SchemaRegistry()

        results = [
            ConnectionError("not ready"),             # first call — fails
            {"semantic_metric_mapping": {             # second call — succeeds
                "category": "mapping",
                "columns": ["metric_id"],
                "qualified": "cc_analytics.semantic_metric_mapping",
                "time_col": None,
            }},
        ]
        call_idx = [0]
        def _fetch():
            r = results[call_idx[0]]
            call_idx[0] += 1
            if isinstance(r, Exception):
                raise r
            return r

        reg._fetch_all = _fetch
        reg.ensure_loaded()                                # fails
        reg._last_failed_at = time.monotonic() - reg._RETRY_THROTTLE_SECS - 1  # advance throttle
        reg.ensure_loaded()                                # recovers

        assert reg.get_table("semantic_metric_mapping") is not None
        assert reg.get_table("semantic_metric_mapping")["category"] == "mapping"


# ===========================================================================
# 6. Planner: registry-first table extraction
# ===========================================================================

class TestPlannerRegistryFirstDetection:
    """Planner must detect tables that only exist in the live registry (non-standard names)."""

    @patch("app.graph_nodes.planner_node._schema_registry")
    def test_mapping_table_extracted_via_registry(self, mock_reg):
        """semantic_metric_mapping is found by registry regex, not just static pattern."""
        mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
        from app.graph_nodes.planner_node import planner_node
        state = planner_node({"user_message": "show row count for semantic_metric_mapping"})
        assert state["literal_table_name"] == "semantic_metric_mapping"
        assert state["intent_type"] == "preview_data"

    @patch("app.graph_nodes.planner_node._schema_registry")
    def test_count_intent_on_mapping_table(self, mock_reg):
        mock_reg.table_name_regex.return_value = _mock_registry().table_name_regex()
        from app.graph_nodes.planner_node import planner_node
        # "show row count" triggers _PREVIEW_VERBS_RE (show + rows?) + has a literal table
        state = planner_node({"user_message": "show row count for domain_semantic_mapping"})
        assert state["literal_table_name"] == "domain_semantic_mapping"
        assert state["intent_type"] == "preview_data"

    @patch("app.graph_nodes.planner_node._schema_registry")
    def test_fallback_to_static_regex_when_registry_empty(self, mock_reg):
        """When registry is empty, static regex must still extract raw_* tables."""
        import re
        mock_reg.table_name_regex.return_value = re.compile(r"(?!)")  # never matches
        from app.graph_nodes.planner_node import planner_node
        state = planner_node({"user_message": "show sample data from raw_customer"})
        # Falls back to _TABLE_NAME_RE — raw_customer matches
        assert state["literal_table_name"] == "raw_customer"
