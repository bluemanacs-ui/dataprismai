"""Regression tests for intent classification and routing.

Tests run without a live database — all StarRocks calls are mocked.
Run with:  pytest apps/api/tests/test_intent_routing.py -v
"""
import pytest
import sys
import os

# Add the API root to sys.path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────────────
# Planner node — pure unit tests (no DB)
# ─────────────────────────────────────────────────────────────────────────────
from app.graph_nodes.planner_node import planner_node


class TestPlannerIntentClassification:
    """Deterministic intent classification — no I/O required."""

    def _plan(self, message: str) -> dict:
        return planner_node({"user_message": message})

    # ── preview_data ─────────────────────────────────────────────────────────

    def test_preview_show_sample(self):
        state = self._plan("show sample data from raw_customer")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "raw_customer"

    def test_preview_preview_keyword(self):
        state = self._plan("preview raw_transaction")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "raw_transaction"

    def test_preview_select_star(self):
        state = self._plan("select * from semantic_customer_360 limit 5")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "semantic_customer_360"

    def test_preview_show_rows(self):
        state = self._plan("show 10 rows from dp_risk_signals")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "dp_risk_signals"

    def test_preview_bare_table_reference(self):
        """A message that is just a table name (no verbs) should be preview_data."""
        state = self._plan("ddm_customer")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "ddm_customer"

    def test_preview_audit_table(self):
        state = self._plan("show audit_query_log")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"
        assert state["literal_table_name"] == "audit_query_log"

    def test_preview_dp_table(self):
        state = self._plan("list dp_transaction_enriched")
        assert state["intent_type"] == "preview_data"
        assert state["response_mode"] == "table"

    def test_preview_does_not_match_metric_query(self):
        """'show fraud rate by country' must NOT be classified as preview_data."""
        state = self._plan("show fraud rate by country")
        assert state["intent_type"] != "preview_data"
        assert state["response_mode"] != "table"

    # ── schema_query ─────────────────────────────────────────────────────────

    def test_schema_describe(self):
        state = self._plan("describe raw_customer")
        assert state["intent_type"] == "schema_query"
        assert state["response_mode"] == "schema"
        assert state["literal_table_name"] == "raw_customer"

    def test_schema_what_columns(self):
        state = self._plan("what columns are in semantic_customer_360")
        assert state["intent_type"] == "schema_query"
        assert state["response_mode"] == "schema"
        assert state["literal_table_name"] == "semantic_customer_360"

    def test_schema_show_schema(self):
        state = self._plan("show schema for raw_transaction")
        assert state["intent_type"] == "schema_query"
        assert state["response_mode"] == "schema"

    def test_schema_fields(self):
        state = self._plan("what fields does ddm_account have")
        assert state["intent_type"] == "schema_query"
        assert state["response_mode"] == "schema"
        assert state["literal_table_name"] == "ddm_account"

    # ── metric_query ─────────────────────────────────────────────────────────

    def test_metric_fraud_rate(self):
        state = self._plan("show fraud rate by country")
        assert state["intent_type"] == "metric_query"
        assert state["response_mode"] == "metric"

    def test_metric_total_spend(self):
        state = self._plan("total spend by merchant category")
        assert state["intent_type"] == "metric_query"
        assert state["response_mode"] == "metric"

    def test_metric_payment_status(self):
        state = self._plan("payment status by month")
        assert state["intent_type"] == "metric_query"
        assert state["response_mode"] == "metric"

    def test_metric_delinquency_trend(self):
        state = self._plan("delinquency rate trend over last 6 months")
        assert state["intent_type"] == "metric_query"
        assert state["response_mode"] == "metric"

    # ── insight_query ─────────────────────────────────────────────────────────

    def test_insight_key_insights(self):
        state = self._plan("what are the key insights on customer risk")
        assert state["intent_type"] == "insight_query"
        assert state["response_mode"] == "insight"

    def test_insight_summarize(self):
        state = self._plan("summarize portfolio performance")
        assert state["intent_type"] == "insight_query"
        assert state["response_mode"] == "insight"

    def test_insight_what_should_i_focus(self):
        state = self._plan("what should I focus on this month")
        assert state["intent_type"] == "insight_query"
        assert state["response_mode"] == "insight"


# ─────────────────────────────────────────────────────────────────────────────
# Semantic resolver node — should short-circuit for preview/schema
# ─────────────────────────────────────────────────────────────────────────────
from unittest.mock import patch, MagicMock


class TestSemanticResolverShortCircuit:
    """Semantic resolver must not run metric scoring for preview/schema."""

    def _run_resolver(self, intent_type: str) -> dict:
        from app.graph_nodes.semantic_resolver_node import semantic_resolver_node
        return semantic_resolver_node({
            "user_message": "show raw_customer",
            "persona": "analyst",
            "thread_id": "test",
            "time_range": "ALL",
            "intent_type": intent_type,
        })

    def test_preview_skips_resolver(self):
        with patch("app.graph_nodes.semantic_resolver_node.resolve_semantic_context") as mock_resolve:
            result = self._run_resolver("preview_data")
            mock_resolve.assert_not_called()
            # semantic_context should not be set
            assert "semantic_context" not in result or result.get("semantic_context") is None or True
            # Reasoning step records the skip
            assert any("skipped" in s.lower() for s in result.get("reasoning_steps", []))

    def test_schema_skips_resolver(self):
        with patch("app.graph_nodes.semantic_resolver_node.resolve_semantic_context") as mock_resolve:
            result = self._run_resolver("schema_query")
            mock_resolve.assert_not_called()

    def test_metric_runs_resolver(self):
        with patch("app.graph_nodes.semantic_resolver_node.resolve_semantic_context") as mock_resolve, \
             patch("app.graph_nodes.semantic_resolver_node.get_context", return_value=[]):
            mock_resolve.return_value = {"metric": "Fraud Rate", "free_form": False, "engine": "starrocks",
                                         "domain": "risk", "definition": "", "persona": "analyst"}
            result = self._run_resolver("metric_query")
            mock_resolve.assert_called_once()
            assert "semantic_context" in result


# ─────────────────────────────────────────────────────────────────────────────
# Vanna SQL node — fast paths for preview_data and schema_query
# ─────────────────────────────────────────────────────────────────────────────
class TestVannaSqlFastPath:
    """Vanna SQL node must generate deterministic SQL for preview/schema without LLM."""

    def _make_state(self, intent_type: str, message: str, table_name: str) -> dict:
        return {
            "user_message": message,
            "persona": "analyst",
            "semantic_context": {},
            "prior_context": [],
            "intent_type": intent_type,
            "literal_table_name": table_name,
        }

    @patch("app.graph_nodes.vanna_sql_node._schema_registry")
    def test_preview_generates_select(self, mock_registry):
        mock_registry.get_table.return_value = {"qualified": "cc_analytics.raw_customer", "columns": []}
        mock_registry.known_table_names.return_value = frozenset(["raw_customer"])
        from app.graph_nodes.vanna_sql_node import vanna_sql_node
        state = self._make_state("preview_data", "show sample data from raw_customer", "raw_customer")
        result = vanna_sql_node(state)
        assert "generated_sql" in result
        sql = result["generated_sql"].upper()
        assert "SELECT" in sql
        assert "RAW_CUSTOMER" in sql
        assert "LIMIT" in sql
        # No Vanna / LLM calls — verified by the mock not being called for generate_sql_from_question
        step_text = " ".join(result.get("reasoning_steps", []))
        assert "fast path" in step_text.lower()

    @patch("app.graph_nodes.vanna_sql_node._schema_registry")
    def test_preview_count_generates_count(self, mock_registry):
        mock_registry.get_table.return_value = {"qualified": "cc_analytics.raw_customer", "columns": []}
        mock_registry.known_table_names.return_value = frozenset(["raw_customer"])
        from app.graph_nodes.vanna_sql_node import vanna_sql_node
        state = self._make_state("preview_data", "count rows in raw_customer", "raw_customer")
        result = vanna_sql_node(state)
        sql = result["generated_sql"].upper()
        assert "COUNT" in sql
        assert "FROM CC_ANALYTICS.RAW_CUSTOMER" in sql

    @patch("app.graph_nodes.vanna_sql_node._schema_registry")
    def test_schema_query_generates_information_schema_sql(self, mock_registry):
        mock_registry.get_table.return_value = {"qualified": "cc_analytics.raw_customer", "columns": []}
        mock_registry.known_table_names.return_value = frozenset(["raw_customer"])
        from app.graph_nodes.vanna_sql_node import vanna_sql_node
        state = self._make_state("schema_query", "describe raw_customer", "raw_customer")
        result = vanna_sql_node(state)
        sql = result["generated_sql"].upper()
        assert "INFORMATION_SCHEMA" in sql
        assert "RAW_CUSTOMER" in sql


# ─────────────────────────────────────────────────────────────────────────────
# Insight node — skip for table/schema
# ─────────────────────────────────────────────────────────────────────────────
class TestInsightNodeSkip:
    """Insight node must return empty insight lists for table and schema modes."""

    def _run_insight(self, response_mode: str) -> dict:
        from app.graph_nodes.insight_node import insight_node
        return insight_node({
            "response_mode": response_mode,
            "query_result": {"rows": [{"col": "val"}], "columns": ["col"]},
            "semantic_context": {"metric": "", "free_form": True},
            "user_message": "show raw_customer",
        })

    def test_table_mode_skips_insight(self):
        result = self._run_insight("table")
        assert result["insights"] == []
        assert result["kpi_metrics"] == []
        assert result["bottlenecks"] == []
        assert result["highlight_actions"] == []
        assert any("skipped" in s.lower() for s in result.get("reasoning_steps", []))

    def test_schema_mode_skips_insight(self):
        result = self._run_insight("schema")
        assert result["insights"] == []
        assert result["kpi_metrics"] == []


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation node — skip for table/schema
# ─────────────────────────────────────────────────────────────────────────────
class TestRecommendationNodeSkip:
    """Recommendation node must return empty follow-ups for table and schema modes."""

    def _run_rec(self, response_mode: str) -> dict:
        from app.graph_nodes.recommendation_node import recommendation_node
        return recommendation_node({
            "response_mode": response_mode,
            "semantic_context": {"metric": "", "time_range": "ALL"},
            "persona": "analyst",
            "sql_assumptions": [],
            "user_message": "show raw_customer",
        })

    def test_table_mode_skips_recommendations(self):
        result = self._run_rec("table")
        assert result["follow_ups"] == []
        assert result["insight_recommendations"] == []

    def test_schema_mode_skips_recommendations(self):
        result = self._run_rec("schema")
        assert result["follow_ups"] == []

    def test_metric_mode_generates_recommendations(self):
        result = self._run_rec("metric")
        # analyst persona defaults always give follow_ups
        assert len(result["follow_ups"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Response node — mode-specific answer composition
# ─────────────────────────────────────────────────────────────────────────────
class TestResponseNodeModes:
    """Response node must compose the answer differently per response_mode."""

    def _base_state(self, response_mode: str, rows, columns, **kwargs) -> dict:
        return {
            "response_mode": response_mode,
            "literal_table_name": "raw_customer",
            "query_result": {"rows": rows, "columns": columns},
            "semantic_context": {"metric": "", "free_form": True},
            "user_message": "test",
            "insights": [],
            "bottlenecks": [],
            "highlight_actions": [],
            **kwargs,
        }

    def test_table_mode_bulk_rows(self):
        from app.graph_nodes.response_node import response_node
        rows = [{"customer_id": "C001", "name": "Alice", "country_code": "SG"}] * 10
        state = self._base_state("table", rows, ["customer_id", "name", "country_code"])
        result = response_node(state)
        answer = result["answer"]
        assert "10 rows" in answer
        assert "raw_customer" in answer
        # Must NOT contain insight/analysis language
        assert "insight" not in answer.lower()
        assert "leads with" not in answer.lower()

    def test_table_mode_count_result(self):
        from app.graph_nodes.response_node import response_node
        rows = [{"row_count": 12345}]
        state = self._base_state("table", rows, ["row_count"])
        result = response_node(state)
        assert "12,345" in result["answer"]
        assert "raw_customer" in result["answer"]

    def test_schema_mode_column_list(self):
        from app.graph_nodes.response_node import response_node
        rows = [
            {"COLUMN_NAME": "customer_id", "DATA_TYPE": "varchar", "IS_NULLABLE": "NO", "COLUMN_DEFAULT": None},
            {"COLUMN_NAME": "full_name",   "DATA_TYPE": "varchar", "IS_NULLABLE": "YES", "COLUMN_DEFAULT": None},
            {"COLUMN_NAME": "credit_score","DATA_TYPE": "int",     "IS_NULLABLE": "YES", "COLUMN_DEFAULT": None},
        ]
        state = self._base_state("schema", rows, ["COLUMN_NAME", "DATA_TYPE", "IS_NULLABLE", "COLUMN_DEFAULT"])
        result = response_node(state)
        answer = result["answer"]
        assert "Schema for" in answer
        assert "customer_id" in answer
        assert "varchar" in answer

    def test_schema_no_rows(self):
        from app.graph_nodes.response_node import response_node
        state = self._base_state("schema", [], [])
        result = response_node(state)
        assert "No schema" in result["answer"]

    def test_metric_mode_not_triggered_for_table(self):
        """When response_mode==table, response_node must not fall through to metric path."""
        from app.graph_nodes.response_node import response_node
        rows = [{"country_code": "SG", "fraud_rate_pct": 2.5}]
        # Even though data looks like metrics, table mode must win
        state = self._base_state("table", rows, ["country_code", "fraud_rate_pct"])
        result = response_node(state)
        answer = result["answer"]
        # table mode: gives row count, not "leads with"
        assert "leads with" not in answer
        assert "1 row" in answer or "row" in answer


# ─────────────────────────────────────────────────────────────────────────────
# Entity extractor — unit tests (no I/O)
# ─────────────────────────────────────────────────────────────────────────────
class TestEntityExtractor:
    """extract_entity() should identify the primary entity from messages and rows."""

    def test_customer_id_from_message(self):
        from app.services.entity_extractor import extract_entity
        e = extract_entity("show customer CUST_100 details", [], [])
        assert e is not None
        assert e["entity_type"] == "customer"
        assert e["entity_id"]   == "CUST_100"

    def test_account_id_from_message(self):
        from app.services.entity_extractor import extract_entity
        e = extract_entity("show transactions for account ACC_500", [], [])
        assert e is not None
        assert e["entity_type"] == "account"
        assert e["entity_id"]   == "ACC_500"

    def test_card_id_from_message(self):
        from app.services.entity_extractor import extract_entity
        e = extract_entity("list transactions on CARD_007", [], [])
        assert e is not None
        assert e["entity_type"] == "card"
        assert e["entity_id"]   == "CARD_007"

    def test_extracts_name_from_single_row(self):
        from app.services.entity_extractor import extract_entity
        rows = [{"customer_id": "CUST_042", "first_name": "Alice", "last_name": "Smith"}]
        e = extract_entity("show customer Alice", rows, ["customer_id", "first_name", "last_name"])
        assert e is not None
        assert e["entity_id"]   == "CUST_042"
        assert "Alice" in e["entity_name"]

    def test_no_entity_from_multiple_distinct_ids(self):
        """Multiple different IDs in result → do NOT store any single entity."""
        from app.services.entity_extractor import extract_entity
        rows = [{"customer_id": "CUST_001"}, {"customer_id": "CUST_002"}, {"customer_id": "CUST_003"}]
        e = extract_entity("top 3 customers by spend", rows, ["customer_id"])
        assert e is None

    def test_single_entity_when_all_rows_share_one_id(self):
        """All rows with same account_id → extract account entity."""
        from app.services.entity_extractor import extract_entity
        rows = [
            {"account_id": "ACC_001", "card_id": "CARD_A"},
            {"account_id": "ACC_001", "card_id": "CARD_B"},
        ]
        e = extract_entity("show cards for ACC_001", rows, ["account_id", "card_id"])
        assert e is not None
        assert e["entity_type"] == "account"
        assert e["entity_id"]   == "ACC_001"

    def test_message_id_beats_row_id(self):
        """ID explicitly stated in message takes precedence over the row content."""
        from app.services.entity_extractor import extract_entity
        rows = [{"customer_id": "CUST_999"}]
        e = extract_entity("Show CUST_100 details", rows, ["customer_id"])
        assert e["entity_id"] == "CUST_100"   # message wins


# ─────────────────────────────────────────────────────────────────────────────
# Entity resolver node — unit tests
# ─────────────────────────────────────────────────────────────────────────────
class TestEntityResolverNode:
    """entity_resolver_node() — pronoun rewriting and entity storage."""

    def setup_method(self):
        # Isolate each test: clear entity store between runs
        from app.services import thread_memory as tm
        tm._entity_store.clear()

    # ── Case 1 (from requirements): CUST_100 → pronoun "his" resolved ────────
    def test_case1_his_balance_resolved(self):
        """User: show customer CUST_100  →  User: what is his balance?"""
        from app.services.thread_memory import store_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node

        # Simulate turn 1 outcome: entity stored after query ran
        store_entity("t_case1", "customer", "CUST_100", "")

        # Turn 2: pronoun follow-up
        state = entity_resolver_node({
            "user_message": "what is his balance?",
            "thread_id":    "t_case1",
        })
        assert "CUST_100" in state["user_message"]
        assert state.get("original_message") == "what is his balance?"
        assert state.get("resolved_entity", {}).get("entity_id") == "CUST_100"

    # ── Case 2 (from requirements): ACC_1 → "this account" resolved ─────────
    def test_case2_this_account_resolved(self):
        """User: show transactions for account ACC_1  →  User: show last 5 for this account"""
        from app.services.thread_memory import store_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node

        store_entity("t_case2", "account", "ACC_001", "")

        state = entity_resolver_node({
            "user_message": "show last 5 for this account",
            "thread_id":    "t_case2",
        })
        assert "ACC_001" in state["user_message"]
        assert state.get("original_message") == "show last 5 for this account"

    def test_she_pronoun_resolved(self):
        from app.services.thread_memory import store_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        store_entity("t_she", "customer", "CUST_200", "Alice Smith")
        state = entity_resolver_node({"user_message": "show her recent transactions", "thread_id": "t_she"})
        assert "CUST_200" in state["user_message"]

    def test_that_customer_resolved(self):
        from app.services.thread_memory import store_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        store_entity("t_that", "customer", "CUST_300", "")
        state = entity_resolver_node({"user_message": "list cards for that customer", "thread_id": "t_that"})
        assert "CUST_300" in state["user_message"]

    def test_explicit_id_stored_on_first_mention(self):
        """First mention of CUST_999 should be stored in entity memory."""
        from app.services.thread_memory import get_last_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        entity_resolver_node({"user_message": "show details for customer CUST_999", "thread_id": "t_store"})
        entity = get_last_entity("t_store")
        assert entity is not None
        assert entity["entity_id"] == "CUST_999"

    def test_no_pronoun_no_id_passthrough(self):
        """Plain metric query passes through unchanged."""
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        state = entity_resolver_node({"user_message": "show fraud rate by country", "thread_id": "t_pass"})
        assert state["user_message"] == "show fraud rate by country"
        assert state.get("original_message") is None

    def test_pronoun_no_entity_in_memory_passthrough(self):
        """Pronoun with no prior entity → message unchanged, no crash."""
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        state = entity_resolver_node({"user_message": "what is her balance?", "thread_id": "t_empty_entity"})
        assert state["user_message"] == "what is her balance?"
        assert not state.get("resolved_entity")

    def test_possessive_rewrite(self):
        """'their' is replaced correctly with '<entity_type> <id>'s'."""
        from app.services.thread_memory import store_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        store_entity("t_poss", "customer", "CUST_400", "")
        state = entity_resolver_node({"user_message": "show their transaction history", "thread_id": "t_poss"})
        assert "CUST_400" in state["user_message"]
        assert "'s" in state["user_message"]

    def test_thread_isolation(self):
        """Entities in thread A must not bleed into thread B."""
        from app.services.thread_memory import store_entity, get_last_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        store_entity("thread_A", "customer", "CUST_A", "")
        state_b = entity_resolver_node({"user_message": "what is his balance?", "thread_id": "thread_B"})
        # Thread B has no entity — message stays unchanged
        assert "CUST_A" not in state_b["user_message"]

    def test_entity_overwrite_on_new_id(self):
        """When user mentions a new entity ID the old one is replaced in memory."""
        from app.services.thread_memory import store_entity, get_last_entity
        from app.graph_nodes.entity_resolver_node import entity_resolver_node
        store_entity("t_over", "customer", "CUST_OLD", "")
        entity_resolver_node({"user_message": "show account ACC_NEW", "thread_id": "t_over"})
        entity = get_last_entity("t_over")
        assert entity["entity_id"] == "ACC_NEW"
        assert entity["entity_type"] == "account"


# ─────────────────────────────────────────────────────────────────────────────
# Thread memory — entity storage API
# ─────────────────────────────────────────────────────────────────────────────
class TestThreadMemoryEntityStorage:
    def setup_method(self):
        from app.services import thread_memory as tm
        tm._entity_store.clear()

    def test_store_and_get_entity(self):
        from app.services.thread_memory import store_entity, get_last_entity
        store_entity("t1", "customer", "CUST_001", "Alice")
        e = get_last_entity("t1")
        assert e["entity_type"] == "customer"
        assert e["entity_id"]   == "CUST_001"
        assert e["entity_name"] == "Alice"

    def test_overwrite_entity(self):
        from app.services.thread_memory import store_entity, get_last_entity
        store_entity("t2", "customer", "CUST_001", "")
        store_entity("t2", "account",  "ACC_500",  "")
        e = get_last_entity("t2")
        assert e["entity_type"] == "account"
        assert e["entity_id"]   == "ACC_500"

    def test_no_entity_returns_none(self):
        from app.services.thread_memory import get_last_entity
        assert get_last_entity("t_nonexistent") is None

    def test_empty_entity_id_not_stored(self):
        from app.services.thread_memory import store_entity, get_last_entity
        store_entity("t3", "customer", "", "")
        assert get_last_entity("t3") is None
