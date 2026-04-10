# =============================================================================
# DataPrismAI — Configuration Schema (Master Definition)
# =============================================================================
# Every configurable parameter in the system is declared here.
# This single source of truth is used by:
#   • ConfigService  — to merge DB overrides with env/default values
#   • GET /config    — to return structured metadata to the frontend
#   • PATCH /config  — to validate updates before writing to DB
#
# Field guide:
#   key          — dot-namespaced identifier, e.g. "llm.model"
#   section      — grouping key for the UI accordion (matches the data flow)
#   label        — human-readable name shown in the UI
#   description  — tooltip / help text shown in the UI
#   default      — hardcoded fallback when neither DB nor env is set
#   env_var      — environment variable that overrides the default
#   input_type   — "text" | "password" | "number" | "boolean" | "select" | "textarea"
#   options      — list of {value, label} for "select" type
#   is_readonly  — shown greyed in UI; cannot be changed via API
#   is_sensitive — value is masked (***) in API responses
#   restart_req  — shows "restart required" badge in UI
# =============================================================================

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfigEntry:
    key: str
    section: str
    label: str
    description: str
    default: str
    env_var: str = ""
    input_type: str = "text"          # text | password | number | boolean | select | textarea
    options: list[dict] = field(default_factory=list)
    is_readonly: bool = False
    is_sensitive: bool = False
    restart_req: bool = False

    def env_default(self) -> str:
        """Return env-var value if set, otherwise the hardcoded default."""
        if self.env_var:
            val = os.getenv(self.env_var)
            if val is not None:
                return val
        return self.default


_MODEL_OPTIONS = [
    {"value": "qwen2.5:7b",   "label": "Qwen 2.5 7B  (fast)"},
    {"value": "qwen2.5:32b",  "label": "Qwen 2.5 32B (accurate)"},
    {"value": "deepseek-r1:7b",  "label": "DeepSeek-R1 7B"},
    {"value": "deepseek-r1:32b", "label": "DeepSeek-R1 32B"},
    {"value": "llama3.2:3b",  "label": "Llama 3.2 3B"},
    {"value": "mistral:7b",   "label": "Mistral 7B"},
]

# ---------------------------------------------------------------------------
# Master list — order determines UI display order within each section
# ---------------------------------------------------------------------------
CONFIG_ENTRIES: list[ConfigEntry] = [

    # ── Application ──────────────────────────────────────────────────────────
    ConfigEntry(
        key="app.name",
        section="application",
        label="Application Name",
        description="Display name shown in the top bar and API title.",
        default="DataPrismAI API",
        env_var="APP_NAME",
    ),
    ConfigEntry(
        key="app.environment",
        section="application",
        label="Environment",
        description="Runtime environment tag. Shown in the top bar badge.",
        default="development",
        input_type="select",
        options=[
            {"value": "development", "label": "Development"},
            {"value": "staging",     "label": "Staging"},
            {"value": "production",  "label": "Production"},
        ],
    ),
    ConfigEntry(
        key="app.version",
        section="application",
        label="Version",
        description="Application version. Managed by CI/CD — not editable.",
        default="1.0.0",
        is_readonly=True,
    ),
    ConfigEntry(
        key="app.cors_origins",
        section="application",
        label="Allowed CORS Origins",
        description="Comma-separated list of frontend origins allowed to call the API.",
        default="http://localhost:3000,http://localhost:3001",
        env_var="ALLOWED_ORIGINS",
        input_type="textarea",
        restart_req=True,
    ),
    ConfigEntry(
        key="app.superset_url",
        section="application",
        label="Superset URL",
        description="Base URL for Apache Superset (optional BI integration).",
        default="http://localhost:8088",
        env_var="SUPERSET_URL",
    ),

    # ── LLM / Ollama ─────────────────────────────────────────────────────────
    ConfigEntry(
        key="llm.ollama_host",
        section="llm",
        label="Ollama Host",
        description="Base URL of the Ollama inference server.",
        default="http://localhost:11434",
        env_var="OLLAMA_HOST",
        restart_req=True,
    ),
    ConfigEntry(
        key="llm.model",
        section="llm",
        label="Primary LLM Model",
        description="Model used for SQL generation, insight, and response composition.",
        default="qwen2.5:32b",
        env_var="OLLAMA_MODEL",
        input_type="select",
        options=_MODEL_OPTIONS,
    ),
    ConfigEntry(
        key="llm.general_model",
        section="llm",
        label="General-Purpose Model",
        description="Lighter model used for guardrail, planner, and general Q&A nodes.",
        default="qwen2.5:7b",
        env_var="OLLAMA_GENERAL_MODEL",
        input_type="select",
        options=_MODEL_OPTIONS,
    ),
    ConfigEntry(
        key="llm.available_models",
        section="llm",
        label="Available Models (comma-separated)",
        description="Comma-separated list of Ollama models available on this server.",
        default="qwen2.5:7b,qwen2.5:32b",
        env_var="OLLAMA_AVAILABLE_MODELS",
    ),
    ConfigEntry(
        key="llm.temperature",
        section="llm",
        label="LLM Temperature",
        description="Sampling temperature (0 = deterministic, 1 = creative).",
        default="0.2",
        input_type="number",
    ),
    ConfigEntry(
        key="llm.sql_temperature",
        section="llm",
        label="SQL Generation Temperature",
        description="Lower temperature for more deterministic SQL output.",
        default="0.05",
        input_type="number",
    ),

    # ── Vanna SQL ─────────────────────────────────────────────────────────────
    ConfigEntry(
        key="vanna.enabled",
        section="vanna",
        label="Enable Vanna SQL",
        description="Use Vanna as the primary SQL generation engine before falling back to direct Ollama.",
        default="false",
        env_var="USE_VANNA",
        input_type="boolean",
    ),
    ConfigEntry(
        key="vanna.model",
        section="vanna",
        label="Vanna Model",
        description="Ollama model used by Vanna for SQL generation.",
        default="qwen2.5:32b",
        env_var="VANNA_MODEL",
        input_type="select",
        options=_MODEL_OPTIONS,
    ),

    # ── StarRocks (OLAP) ──────────────────────────────────────────────────────
    ConfigEntry(
        key="starrocks.host",
        section="starrocks",
        label="StarRocks Host",
        description="Hostname or IP of the StarRocks FE node.",
        default="localhost",
        env_var="STARROCKS_HOST",
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.port",
        section="starrocks",
        label="StarRocks Port (MySQL wire)",
        description="MySQL wire protocol port (default 9030).",
        default="9030",
        env_var="STARROCKS_PORT",
        input_type="number",
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.user",
        section="starrocks",
        label="StarRocks User",
        description="Database user for StarRocks connections.",
        default="root",
        env_var="STARROCKS_USER",
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.password",
        section="starrocks",
        label="StarRocks Password",
        description="Password for the StarRocks database user.",
        default="",
        env_var="STARROCKS_PASSWORD",
        input_type="password",
        is_sensitive=True,
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.database",
        section="starrocks",
        label="StarRocks Database",
        description="Target database / catalog in StarRocks.",
        default="cc_analytics",
        env_var="STARROCKS_DATABASE",
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.pool_size",
        section="starrocks",
        label="Connection Pool Size",
        description="Max simultaneous StarRocks connections in the pool.",
        default="20",
        input_type="number",
        restart_req=True,
    ),
    ConfigEntry(
        key="starrocks.query_timeout",
        section="starrocks",
        label="Query Timeout (seconds)",
        description="Maximum seconds before a StarRocks query is cancelled.",
        default="30",
        input_type="number",
    ),
    ConfigEntry(
        key="starrocks.max_rows",
        section="starrocks",
        label="Max Result Rows",
        description="Maximum rows returned from any single query execution.",
        default="1000",
        input_type="number",
    ),

    # ── PostgreSQL (Operational) ───────────────────────────────────────────────
    ConfigEntry(
        key="postgres.url",
        section="postgres",
        label="PostgreSQL Connection URL",
        description="Full SQLAlchemy connection string for the operational Postgres database. Managed via DATABASE_URL env var.",
        default="postgresql://dataprismai:dataprismai@localhost:5432/dataprismai",
        env_var="DATABASE_URL",
        input_type="password",
        is_sensitive=True,
        is_readonly=True,
        restart_req=True,
    ),
    ConfigEntry(
        key="postgres.pool_pre_ping",
        section="postgres",
        label="Pool Pre-Ping",
        description="Test connections before use to detect stale connections.",
        default="true",
        input_type="boolean",
        is_readonly=True,
    ),

    # ── Guardrail ─────────────────────────────────────────────────────────────
    ConfigEntry(
        key="guardrail.enabled",
        section="guardrail",
        label="Enable Guardrail",
        description="When disabled, all queries pass through without classification checks.",
        default="true",
        input_type="boolean",
    ),
    ConfigEntry(
        key="guardrail.allow_greetings",
        section="guardrail",
        label="Respond to Greetings",
        description="When enabled, greetings trigger a friendly response instead of being blocked.",
        default="true",
        input_type="boolean",
    ),
    ConfigEntry(
        key="guardrail.max_message_length",
        section="guardrail",
        label="Max Message Length (chars)",
        description="Messages longer than this are rejected as invalid input.",
        default="2000",
        input_type="number",
    ),
    ConfigEntry(
        key="guardrail.gibberish_vowel_threshold",
        section="guardrail",
        label="Gibberish Vowel Ratio Threshold",
        description="Words with vowel-to-alpha ratio below this are flagged as gibberish (0.0–1.0).",
        default="0.1",
        input_type="number",
    ),
    ConfigEntry(
        key="guardrail.min_word_length",
        section="guardrail",
        label="Minimum Token Length for Gibberish Check",
        description="Only tokens longer than this are checked for gibberish patterns.",
        default="6",
        input_type="number",
    ),

    # ── Planner ───────────────────────────────────────────────────────────────
    ConfigEntry(
        key="planner.default_intent",
        section="planner",
        label="Default Intent Type",
        description="Fallback intent when the planner cannot classify the query.",
        default="metric_query",
        input_type="select",
        options=[
            {"value": "metric_query",  "label": "Metric Query"},
            {"value": "insight_query", "label": "Insight Query"},
            {"value": "preview_data",  "label": "Data Preview"},
        ],
    ),
    ConfigEntry(
        key="planner.enable_llm_fallback",
        section="planner",
        label="Enable LLM Planner Fallback",
        description="Use LLM to classify intent when rule-based matching is inconclusive.",
        default="true",
        input_type="boolean",
    ),

    # ── Semantic Layer ────────────────────────────────────────────────────────
    ConfigEntry(
        key="semantic.catalog_source",
        section="semantic",
        label="Catalog Source",
        description="Where to load semantic catalog metadata from.",
        default="starrocks",
        input_type="select",
        options=[
            {"value": "starrocks", "label": "StarRocks (live)"},
            {"value": "static",    "label": "Static DDL files"},
        ],
    ),
    ConfigEntry(
        key="semantic.schema_cache_ttl",
        section="semantic",
        label="Schema Cache TTL (seconds)",
        description="How long the SchemaRegistry caches live table metadata.",
        default="300",
        input_type="number",
    ),
    ConfigEntry(
        key="semantic.max_tables_in_prompt",
        section="semantic",
        label="Max Tables in SQL Prompt",
        description="Maximum number of table schemas injected into the SQL generation prompt.",
        default="10",
        input_type="number",
    ),
    ConfigEntry(
        key="semantic.include_sample_values",
        section="semantic",
        label="Include Sample Values in Prompt",
        description="Inject sample enum values into the SQL prompt for better accuracy.",
        default="true",
        input_type="boolean",
    ),

    # ── Query Router ──────────────────────────────────────────────────────────
    ConfigEntry(
        key="router.primary_engine",
        section="router",
        label="Primary Query Engine",
        description="Engine used for all SQL execution by default.",
        default="starrocks",
        input_type="select",
        options=[
            {"value": "starrocks", "label": "StarRocks"},
            {"value": "trino",     "label": "Trino (federation)"},
        ],
    ),
    ConfigEntry(
        key="router.trino_url",
        section="router",
        label="Trino URL",
        description="Base URL for the Trino coordinator (used when primary engine is Trino).",
        default="",
    ),

    # ── Result Evaluator ──────────────────────────────────────────────────────
    ConfigEntry(
        key="evaluator.max_retry",
        section="evaluator",
        label="Max SQL Retry Attempts",
        description="How many times to retry SQL generation when the result is empty.",
        default="1",
        input_type="number",
    ),
    ConfigEntry(
        key="evaluator.empty_triggers_retry",
        section="evaluator",
        label="Empty Result Triggers Retry",
        description="When enabled, an empty result set triggers SQL regeneration.",
        default="true",
        input_type="boolean",
    ),

    # ── Persona ───────────────────────────────────────────────────────────────
    ConfigEntry(
        key="persona.default",
        section="persona",
        label="Default Persona",
        description="Persona applied when the user has not explicitly chosen one.",
        default="analyst",
        input_type="select",
        options=[
            {"value": "analyst",               "label": "Data Analyst"},
            {"value": "fraud_analyst",         "label": "Fraud Analyst"},
            {"value": "cfo",                   "label": "CFO"},
            {"value": "finance_user",          "label": "Finance User"},
            {"value": "regional_finance_user", "label": "Regional Finance User"},
            {"value": "regional_risk_user",    "label": "Regional Risk User"},
            {"value": "retail_user",           "label": "Retail User"},
            {"value": "manager",               "label": "Manager"},
            {"value": "product",               "label": "Product"},
            {"value": "engineer",              "label": "Engineer"},
            {"value": "admin",                 "label": "Admin"},
        ],
    ),
    ConfigEntry(
        key="persona.available",
        section="persona",
        label="Available Personas",
        description="Comma-separated list of available persona identifiers (file-based — read only).",
        default="analyst,fraud_analyst,cfo,finance_user,regional_finance_user,regional_risk_user,retail_user,manager,product,engineer,admin",
        is_readonly=True,
    ),

    # ── Visualization ─────────────────────────────────────────────────────────
    ConfigEntry(
        key="viz.default_chart_type",
        section="visualization",
        label="Default Chart Type",
        description="Chart type used when the recommendation engine has no preference.",
        default="bar",
        input_type="select",
        options=[
            {"value": "bar",      "label": "Bar"},
            {"value": "line",     "label": "Line"},
            {"value": "pie",      "label": "Pie"},
            {"value": "scatter",  "label": "Scatter"},
            {"value": "heatmap",  "label": "Heatmap"},
        ],
    ),
    ConfigEntry(
        key="viz.max_data_points",
        section="visualization",
        label="Max Visualized Data Points",
        description="Maximum data points rendered by ECharts before sampling is applied.",
        default="500",
        input_type="number",
    ),
    ConfigEntry(
        key="viz.echarts_theme",
        section="visualization",
        label="ECharts Theme",
        description="Visual theme applied to ECharts renders.",
        default="dark",
        input_type="select",
        options=[
            {"value": "dark",  "label": "Dark"},
            {"value": "light", "label": "Light"},
        ],
    ),
]

# Fast lookup by key
CONFIG_MAP: dict[str, ConfigEntry] = {e.key: e for e in CONFIG_ENTRIES}

# Section metadata (order + display labels)
SECTION_META: dict[str, dict] = {
    "application":   {"label": "Application",         "icon": "🏛️",  "description": "Core application identity and CORS settings"},
    "llm":           {"label": "LLM / Ollama",        "icon": "🤖",  "description": "Language model host, model selection and sampling parameters"},
    "vanna":         {"label": "Vanna SQL",           "icon": "🧠",  "description": "Vanna-powered SQL generation engine"},
    "starrocks":     {"label": "StarRocks (OLAP DB)", "icon": "🗃️",  "description": "Analytical database connection and pool settings"},
    "postgres":      {"label": "PostgreSQL (Op. DB)", "icon": "🐘",  "description": "Operational metadata store — managed via environment"},
    "guardrail":     {"label": "Guardrail",           "icon": "🛡️",  "description": "Input validation, intent classification filters"},
    "planner":       {"label": "Planner",             "icon": "🗓️",  "description": "Intent routing rules and LLM fallback behaviour"},
    "semantic":      {"label": "Semantic Layer",      "icon": "📐",  "description": "Schema registry, catalog source and prompt injection"},
    "router":        {"label": "Query Router",        "icon": "🔀",  "description": "Execution engine routing and Trino federation"},
    "evaluator":     {"label": "Result Evaluator",    "icon": "🔍",  "description": "SQL retry policy and empty-result handling"},
    "persona":       {"label": "Persona",             "icon": "🎭",  "description": "Default persona and available persona identifiers"},
    "visualization": {"label": "Visualization",       "icon": "📊",  "description": "Chart type defaults and ECharts rendering options"},
}
