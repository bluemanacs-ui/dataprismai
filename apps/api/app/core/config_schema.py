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

    # ── Business Context ──────────────────────────────────────────────────────
    ConfigEntry(
        key="business.company_name",
        section="business",
        label="Company / Platform Name",
        description="Name of the organisation or platform. Used in AI responses and prompts.",
        default="DataPrismAI",
    ),
    ConfigEntry(
        key="business.industry",
        section="business",
        label="Industry",
        description="Primary industry vertical — used in prompt context to focus AI reasoning.",
        default="Banking",
        input_type="select",
        options=[
            {"value": "Banking",          "label": "Banking & Financial Services"},
            {"value": "Insurance",        "label": "Insurance"},
            {"value": "Retail",           "label": "Retail & E-Commerce"},
            {"value": "Telecom",          "label": "Telecommunications"},
            {"value": "Healthcare",       "label": "Healthcare"},
            {"value": "Manufacturing",    "label": "Manufacturing"},
            {"value": "General",          "label": "General Enterprise"},
        ],
    ),
    ConfigEntry(
        key="business.domain_label",
        section="business",
        label="Analytics Domain Label",
        description="Short label for the analytics domain shown in prompts and UI (e.g. 'Credit Card Analytics').",
        default="Credit Card Analytics",
    ),
    ConfigEntry(
        key="business.countries_in_scope",
        section="business",
        label="Countries in Scope (comma-separated ISO codes)",
        description="Country codes available in the data. Used in prompt context and query routing.",
        default="SG,MY,IN",
    ),
    ConfigEntry(
        key="business.currency_default",
        section="business",
        label="Default Currency",
        description="ISO 4217 currency code used when no currency is specified in queries.",
        default="USD",
    ),
    ConfigEntry(
        key="business.data_year",
        section="business",
        label="Data Reference Year",
        description="Year of the primary dataset. Injected into SQL prompts to ground time references.",
        default="2025",
        input_type="number",
    ),
    ConfigEntry(
        key="business.fiscal_year_start_month",
        section="business",
        label="Fiscal Year Start Month",
        description="Month number (1–12) when the fiscal year begins.",
        default="1",
        input_type="number",
    ),
    ConfigEntry(
        key="business.extra_context",
        section="business",
        label="Additional Business Context",
        description="Free-form business context injected into all AI prompts (e.g. product scope, known data caveats).",
        default="",
        input_type="textarea",
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
        key="semantic.database_name",
        section="semantic",
        label="Analytics Database Name",
        description="StarRocks database that all SQL queries run against (used in table prefix and schema context).",
        default="cc_analytics",
        env_var="STARROCKS_DATABASE",
    ),
    ConfigEntry(
        key="semantic.allowed_table_prefixes",
        section="semantic",
        label="Allowed Table Prefixes (comma-separated)",
        description="Only tables with these prefixes are exposed to the LLM. Prevents access to internal/system tables.",
        default="semantic_,dp_,raw_,ddm_,audit_",
    ),
    ConfigEntry(
        key="semantic.preferred_table_strategy",
        section="semantic",
        label="Preferred Table Strategy",
        description="Controls SQL generation preference: semantic_ tables (pre-aggregated, fast) vs raw_ tables (full detail).",
        default="semantic_first",
        input_type="select",
        options=[
            {"value": "semantic_first", "label": "Semantic tables first (recommended)"},
            {"value": "raw_first",      "label": "Raw tables first (full detail)"},
            {"value": "auto",           "label": "Auto (planner decides)"},
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
    ConfigEntry(
        key="evaluator.empty_result_message",
        section="evaluator",
        label="Empty Result Message",
        description="Message shown to the user when the query returns no rows after all retries.",
        default="No data found for the specified criteria. Try broadening your filters or adjusting the time range.",
        input_type="textarea",
    ),
    ConfigEntry(
        key="evaluator.sql_error_message",
        section="evaluator",
        label="SQL Error Message",
        description="Message shown to the user when SQL execution fails.",
        default="The query could not be executed. Please rephrase your question or contact support.",
        input_type="textarea",
    ),

    # ── Insight Analytics ─────────────────────────────────────────────────────
    ConfigEntry(
        key="insight.risk_threshold_fraud_rate",
        section="insight",
        label="Fraud Rate Alert Threshold (%)",
        description="Fraud rate above this % triggers a risk alert in the insight panel.",
        default="15.0",
        input_type="number",
    ),
    ConfigEntry(
        key="insight.risk_threshold_dispute_rate",
        section="insight",
        label="Dispute Rate Alert Threshold (%)",
        description="Dispute rate above this % triggers a risk alert.",
        default="5.0",
        input_type="number",
    ),
    ConfigEntry(
        key="insight.risk_threshold_delinquency_rate",
        section="insight",
        label="Delinquency Rate Alert Threshold (%)",
        description="Delinquency rate above this % triggers a risk alert.",
        default="10.0",
        input_type="number",
    ),
    ConfigEntry(
        key="insight.max_kpi_cards",
        section="insight",
        label="Max KPI Cards Displayed",
        description="Maximum number of KPI metric cards shown in the insight panel.",
        default="8",
        input_type="number",
    ),
    ConfigEntry(
        key="insight.max_bottleneck_alerts",
        section="insight",
        label="Max Bottleneck Alerts",
        description="Maximum number of bottleneck / anomaly alerts shown per response.",
        default="3",
        input_type="number",
    ),

    # ── Prompting & Reasoning ─────────────────────────────────────────────────
    ConfigEntry(
        key="prompt.app_identity",
        section="prompt",
        label="AI Identity Statement",
        description="Opening sentence used in every LLM system prompt. Change to rebrand the AI persona.",
        default="You are DataPrismAI, an enterprise GenBI insight assistant.",
        input_type="textarea",
    ),
    ConfigEntry(
        key="prompt.prior_turns",
        section="prompt",
        label="Prior Conversation Turns in Context",
        description="Number of prior conversation turns injected into the SQL prompt for pronoun resolution.",
        default="3",
        input_type="number",
    ),
    ConfigEntry(
        key="prompt.narrative_sample_rows",
        section="prompt",
        label="Narrative Sample Rows",
        description="Number of result rows shown to the LLM when generating a narrative answer.",
        default="8",
        input_type="number",
    ),
    ConfigEntry(
        key="prompt.narrative_max_insights",
        section="prompt",
        label="Max Insights in Narrative",
        description="Maximum number of statistical insights passed into the LLM narrative prompt.",
        default="4",
        input_type="number",
    ),
    ConfigEntry(
        key="prompt.sql_extra_rules",
        section="prompt",
        label="Additional SQL Generation Rules",
        description="Extra rules appended to the SQL generation system prompt. One rule per line.",
        default="",
        input_type="textarea",
    ),
    ConfigEntry(
        key="prompt.insight_extra_rules",
        section="prompt",
        label="Additional Insight / Narrative Rules",
        description="Extra rules appended to the narrative response prompt. One rule per line.",
        default="",
        input_type="textarea",
    ),
    ConfigEntry(
        key="prompt.forbidden_sql_statements",
        section="prompt",
        label="Forbidden SQL Statement Types",
        description="Comma-separated SQL statement types that are never allowed in generated SQL.",
        default="INSERT,UPDATE,DELETE,DROP,ALTER,CREATE,TRUNCATE",
        is_readonly=True,
    ),

    # ── Graph Runtime (LangGraph) ─────────────────────────────────────────────
    ConfigEntry(
        key="graph.max_history_turns",
        section="graph",
        label="Thread Memory Max Turns",
        description="Maximum number of conversation turns stored per session thread.",
        default="20",
        input_type="number",
    ),
    ConfigEntry(
        key="graph.entity_id_prefixes",
        section="graph",
        label="Entity ID Prefixes (comma-separated)",
        description="Prefixes used to identify entity IDs in user queries (e.g. CUST_, ACC_). Determines which table lookup to use.",
        default="CUST_,ACC_,CARD_,TXN_,MERCH_",
    ),
    ConfigEntry(
        key="graph.table_name_prefixes",
        section="graph",
        label="Known Table Name Prefixes (comma-separated)",
        description="Table prefixes that the planner uses to identify table-direct queries.",
        default="raw_,ddm_,dp_,semantic_,audit_",
    ),
    ConfigEntry(
        key="graph.enable_entity_resolver",
        section="graph",
        label="Enable Entity Resolver Node",
        description="Resolve pronouns and entity IDs (CUST_, ACC_, etc.) before SQL generation.",
        default="true",
        input_type="boolean",
    ),
    ConfigEntry(
        key="graph.enable_sql_validator",
        section="graph",
        label="Enable SQL Validator Node",
        description="Validate generated SQL before execution (catches syntax errors early).",
        default="true",
        input_type="boolean",
    ),
    ConfigEntry(
        key="graph.enable_chart_recommendation",
        section="graph",
        label="Enable Chart Recommendation Node",
        description="Automatically recommend chart types based on query results.",
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
    "application":   {"label": "Application",              "icon": "🏛️",  "description": "Core application identity and CORS settings"},
    "business":      {"label": "Business Context",         "icon": "🏢",  "description": "Industry, domain label, countries, fiscal year, and free-form business context injected into all AI prompts"},
    "llm":           {"label": "LLM / Ollama",             "icon": "🤖",  "description": "Language model host, model selection and sampling parameters"},
    "vanna":         {"label": "Vanna SQL",                "icon": "🧠",  "description": "Vanna-powered SQL generation engine"},
    "starrocks":     {"label": "StarRocks (OLAP DB)",      "icon": "🗃️",  "description": "Analytical database connection and pool settings"},
    "postgres":      {"label": "PostgreSQL (Op. DB)",      "icon": "🐘",  "description": "Operational metadata store — managed via environment"},
    "semantic":      {"label": "Semantic Layer",           "icon": "📐",  "description": "Database, allowed tables, schema registry, catalog source and prompt injection strategy"},
    "guardrail":     {"label": "Guardrail",                "icon": "🛡️",  "description": "Input validation, message length, intent filters and data keyword lists"},
    "planner":       {"label": "Planner",                  "icon": "🗓️",  "description": "Intent routing rules, entity prefix recognition and LLM fallback behaviour"},
    "router":        {"label": "Query Router",             "icon": "🔀",  "description": "Execution engine routing and Trino federation"},
    "evaluator":     {"label": "Result Evaluator",         "icon": "🔍",  "description": "SQL retry policy, empty-result handling and user-facing error messages"},
    "insight":       {"label": "Insight Analytics",        "icon": "💡",  "description": "Risk alert thresholds, KPI card limits and anomaly detection settings"},
    "prompt":        {"label": "Prompting & Reasoning",    "icon": "✍️",  "description": "AI identity, system prompt rules, prior context turns, narrative sampling, and extra custom rules"},
    "graph":         {"label": "Graph Runtime (LangGraph)","icon": "🕸️",  "description": "LangGraph node enable/disable switches, thread memory size, and entity ID configuration"},
    "persona":       {"label": "Persona",                  "icon": "🎭",  "description": "Default persona and available persona identifiers"},
    "visualization": {"label": "Visualization",            "icon": "📊",  "description": "Chart type defaults and ECharts rendering options"},
}
