"use client";

import React, { useState } from "react";

type HelpTab = "refarch" | "userguide" | "techspec" | "versions";

const TABS: { id: HelpTab; label: string; icon: string }[] = [
  { id: "refarch",   label: "Reference Architecture", icon: "🏗" },
  { id: "userguide", label: "User Guide",              icon: "📖" },
  { id: "techspec",  label: "Tech Spec",               icon: "⚙" },
  { id: "versions",  label: "Versions",                icon: "🏷" },
];

// ── Version manifest ───────────────────────────────────────────────────────
const APP_VERSION = "1.0.0";

const COMPONENT_VERSIONS: { category: string; items: { name: string; version: string; description: string }[] }[] = [
  {
    category: "Application",
    items: [
      { name: "DataPrismAI", version: APP_VERSION, description: "GenBI banking analytics platform — April 2026" },
    ],
  },
  {
    category: "Frontend",
    items: [
      { name: "Next.js",      version: "16.2.2",  description: "React full-stack framework (App Router)" },
      { name: "React",        version: "19.2.4",  description: "UI component library" },
      { name: "TypeScript",   version: "5.x",     description: "Typed JavaScript superset" },
      { name: "Tailwind CSS", version: "4.x",     description: "Utility-first CSS framework" },
      { name: "ECharts",      version: "6.0.0",   description: "Data visualisation — bar, line, pie, scatter, heatmap" },
      { name: "ReactFlow",    version: "12.10.2", description: "Node-graph visualisation" },
    ],
  },
  {
    category: "Backend / API",
    items: [
      { name: "FastAPI",           version: "0.135.3", description: "Python async REST framework" },
      { name: "Starlette",         version: "1.0.0",   description: "ASGI foundation" },
      { name: "Uvicorn",           version: "0.42.0",  description: "ASGI web server with uvloop" },
      { name: "Python",            version: "3.12",    description: "Runtime" },
      { name: "SQLAlchemy",        version: "2.0.48",  description: "ORM + StarRocks/PostgreSQL connector" },
      { name: "Pydantic",          version: "2.12.5",  description: "Request/response validation" },
      { name: "LangGraph",         version: "1.1.5",   description: "Stateful multi-node agent graph" },
      { name: "LangGraph Checkpoint", version: "4.0.1", description: "Thread-level state persistence" },
      { name: "LangChain Core",    version: "1.2.25",  description: "LLM interaction primitives" },
      { name: "Vanna",             version: "2.0.2",   description: "RAG-augmented NL-to-SQL engine" },
      { name: "Ollama (client)",   version: "0.6.1",   description: "Local Ollama API client" },
      { name: "Pandas",            version: "3.0.2",   description: "Result-set processing" },
      { name: "SQLparse",          version: "0.5.5",   description: "SQL syntax parsing + validation" },
      { name: "Alembic",           version: "1.18.4",  description: "Database migration tool" },
      { name: "Plotly",            version: "6.6.0",   description: "Server-side chart config generation" },
    ],
  },
  {
    category: "AI / LLM Runtime",
    items: [
      { name: "Ollama",        version: "—",         description: "Local LLM runtime — GPU-accelerated, ~8 s inference" },
      { name: "qwen2.5:7b",   version: "7B params", description: "Primary inference model (default)" },
      { name: "qwen2.5:32b",  version: "32B params", description: "High-accuracy model (switchable at runtime)" },
      { name: "Vanna",        version: "2.0.2",     description: "Fine-tuned NL-to-SQL on StarRocks DDL + sample queries" },
    ],
  },
  {
    category: "Data Layer",
    items: [
      { name: "StarRocks",    version: "3.x",  description: "MPP OLAP engine — cc_analytics DB (50 tables, 7 layers)" },
      { name: "PostgreSQL",   version: "15.x", description: "Operational store — sessions, users, audit, reports" },
      { name: "Trino",        version: "—",    description: "Federated query engine (optional / future)" },
    ],
  },
  {
    category: "Infrastructure",
    items: [
      { name: "Docker Compose", version: "—",    description: "Local orchestration — api, web, starrocks, postgres, trino" },
      { name: "LangSmith",      version: "0.7.25", description: "LangGraph tracing + observability" },
    ],
  },
];

// ── User Guide ─────────────────────────────────────────────────────────────
function UserGuide() {
  return (
    <div className="space-y-6 text-sm" style={{ color: "var(--foreground)" }}>
      <Section title="Getting Started">
        <p style={{ color: "var(--muted)" }}>DataPrismAI lets you explore your banking data using plain English. Log in, pick your persona, and start asking questions in the chat.</p>
        <ol className="list-decimal ml-4 space-y-1 mt-2" style={{ color: "var(--muted)" }}>
          <li>Log in with your platform credentials (demo: any name + role).</li>
          <li>Your <strong style={{ color: "var(--foreground)" }}>persona</strong> scopes your metrics and data access (Fraud Analyst, Finance, Retail, etc.).</li>
          <li>Type a question like <em>&ldquo;Show top 10 transactions by amount this month&rdquo;</em> and press Enter.</li>
          <li>DataPrismAI generates SQL, queries StarRocks, and returns a rich answer card with charts, insights, and follow-up suggestions.</li>
        </ol>
      </Section>

      <Section title="Query Modes">
        <table className="w-full text-xs border-collapse mt-1">
          <thead>
            <tr style={{ color: "var(--accent-1)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Mode</th>
              <th className="text-left py-1">Behaviour</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["⚡ Pattern", "Deterministic only — pre-built SQL patterns, zero LLM calls. Fastest, most consistent."],
              ["★ Hybrid (default)", "Pattern-first with LLM fallback. Recommended for all daily usage."],
              ["🤖 LLM", "Skips all patterns; enriches with full data dictionary context and goes straight to Vanna / Ollama. Best for complex or novel questions."],
            ].map(([m, d]) => (
              <tr key={m} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-semibold whitespace-nowrap" style={{ color: "var(--foreground)" }}>{m}</td>
                <td className="py-1">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs mt-2" style={{ color: "var(--muted)" }}>Switch modes with the ⚡ ★ 🤖 pills in the top bar — active mode highlighted in green.</p>

        {/* Example questions per mode */}
        <div className="mt-4 space-y-4">
          {[
            {
              mode: "⚡ Pattern — Example Questions",
              color: "#f59e0b",
              questions: [
                "Show total spend by merchant category this month",
                "What is the fraud rate by country?",
                "Show top 10 customers by MTD spend",
                "Show payment status distribution across all accounts",
                "Show monthly transaction count trend",
                "What is the delinquency rate by segment?",
              ],
            },
            {
              mode: "★ Hybrid — Example Questions",
              color: "#00A551",
              questions: [
                "Show portfolio KPIs this quarter",
                "Which customers are overdue on CC payments?",
                "Show top merchants by transaction volume this month",
                "What is the fraud trend by country over the last 3 months?",
                "Show deposit balance breakdown by product type",
                "Which loan segment has the highest NPL rate?",
              ],
            },
            {
              mode: "🤖 LLM — Example Questions",
              color: "#818cf8",
              questions: [
                "Which customer segments have the highest wallet share across CC, deposits, and loans?",
                "What factors correlate with high loan default risk in the SG portfolio?",
                "Compare CC spend growth vs deposit balance growth by customer segment this year",
                "Which customers are likely to churn based on recent payment behaviour?",
                "Show me an end-to-end risk profile for customers with both overdue CC and overdue loans",
                "What is the YoY revenue trend broken down by product line and legal entity?",
              ],
            },
          ].map(({ mode, color, questions }) => (
            <div key={mode}>
              <div className="text-[10px] font-semibold uppercase tracking-widest mb-1" style={{ color }}>{mode}</div>
              <ul className="list-disc ml-4 space-y-0.5" style={{ color: "var(--muted)" }}>
                {questions.map((q) => <li key={q} className="text-xs italic">&ldquo;{q}&rdquo;</li>)}
              </ul>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Chat Interface">
        <ul className="list-disc ml-4 space-y-1" style={{ color: "var(--muted)" }}>
          <li><strong style={{ color: "var(--foreground)" }}>Natural Language</strong> — ask anything; the AI resolves metrics, entities, and dimensions automatically.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Insight Cards</strong> — every answer includes AI-generated insights, KPI highlights, and bottleneck flags.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Follow-up Suggestions</strong> — click any suggestion below an answer to drill down instantly.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Charts</strong> — qualifying results are auto-visualised (bar, line, pie, scatter, heatmap).</li>
          <li><strong style={{ color: "var(--foreground)" }}>SQL &amp; Reasoning</strong> — expand <em>Details</em> on any card to see the generated SQL, semantic context, and chain-of-thought steps.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Entity Memory</strong> — mention a customer or account once; follow-up questions resolve pronouns automatically (e.g. &ldquo;what about <em>their</em> balance?&rdquo;).</li>
          <li><strong style={{ color: "var(--foreground)" }}>Time Range</strong> — filter answers to L7D, L1M, LQ, L1Y, or ALL via the time selector.</li>
        </ul>
      </Section>

      <Section title="Data Explorer">
        <p style={{ color: "var(--muted)" }}>Browse the full 50-table data estate via the <strong style={{ color: "var(--foreground)" }}>Data Explorer</strong> in the sidebar (compass icon). Five tabs are available:</p>
        <ul className="list-disc ml-4 mt-1 space-y-1" style={{ color: "var(--muted)" }}>
          <li><strong style={{ color: "var(--foreground)" }}>Datasets</strong> — 50 tables grouped into 7 layers (Semantic · DP · DDM · Raw · Audit · Config · Meta). All groups collapsed by default; click to expand or search to auto-open matches.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Profiling</strong> — per-table column stats: null %, distinct count, min/max/avg, key type (PK/UK/IDX), and top-value distribution bars.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Models (ERD)</strong> — interactive entity-relationship diagram. Drag cards to rearrange; FK lines follow. Cross-layer references shown as ghost cards. &ldquo;↺ Reset Layout&rdquo; restores the grid.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Semantic Layer</strong> — metric catalog, entity inventory, and cross-layer join map.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Dictionary</strong> — business-friendly column descriptions and data stewardship context for all 36 documented tables.</li>
        </ul>
      </Section>

      <Section title="Data Architecture — 7 Layers">
        <table className="w-full text-xs border-collapse mt-1">
          <thead>
            <tr style={{ color: "var(--accent-1)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Layer</th>
              <th className="text-left pr-4 py-1">Prefix</th>
              <th className="text-left pr-4 py-1">Tables</th>
              <th className="text-left py-1">Purpose</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["🧠 Semantic",  "semantic_", "13", "BI-ready views — metrics, KPIs surfaced for chat"],
              ["📦 Data Products", "dp_",  "11", "Domain-aligned aggregated business tables"],
              ["🏛 DDM",       "ddm_",     "7",  "Conformed dimensional model — typed, validated"],
              ["📥 Raw",       "raw_",     "16", "Ingestion layer — source records, no transforms"],
              ["🔍 Audit",     "audit_",   "6",  "Pipeline runs, data quality, query audit logs"],
              ["⚙ Config",    "(no pfx)", "5",  "Domain routing, intent mapping, access control"],
              ["📋 Meta",      "dic_",     "8",  "Dictionary, semantic catalog, query history"],
            ].map(([l, p, c, d]) => (
              <tr key={l} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-medium" style={{ color: "var(--foreground)" }}>{l}</td>
                <td className="pr-4 py-1 font-mono text-[10px]" style={{ color: "var(--accent-2)" }}>{p}</td>
                <td className="pr-4 py-1 text-center" style={{ color: "var(--accent-1)" }}>{c}</td>
                <td className="py-1">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Personas">
        <table className="w-full text-xs border-collapse mt-1">
          <thead>
            <tr style={{ color: "var(--accent-1)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Persona</th>
              <th className="text-left py-1">Focus Area</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["Fraud Analyst",     "Suspicious transactions, fraud rates, chargebacks, alert trends"],
              ["Finance User",      "Portfolio KPIs, delinquency, P&L metrics, MTD vs prior-period"],
              ["Regional Finance",  "Country-level KPIs, regional portfolio benchmarking"],
              ["Regional Risk",     "Cross-region fraud and delinquency heat maps"],
              ["Retail User",       "Customer spend, payment status, segment breakdowns"],
              ["Analyst (default)", "General exploration — all metrics and layers accessible"],
            ].map(([p, f]) => (
              <tr key={p} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-medium" style={{ color: "var(--foreground)" }}>{p}</td>
                <td className="py-1">{f}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Reports & Audit">
        <ul className="list-disc ml-4 space-y-1" style={{ color: "var(--muted)" }}>
          <li><strong style={{ color: "var(--foreground)" }}>Reports</strong> — all successful query results are auto-saved. Re-run from the Reports panel.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Audit Log</strong> — every query, login, and navigation event is recorded. Admins can review the full trail for compliance. Stored in PostgreSQL <code>audit_query_log</code>.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Query History</strong> — recent queries shown in the sidebar; click to replay instantly.</li>
        </ul>
      </Section>
    </div>
  );
}

// ── Tech Spec ──────────────────────────────────────────────────────────────
function TechSpec() {
  return (
    <div className="space-y-6 text-sm" style={{ color: "var(--foreground)" }}>
      <Section title="Architecture Overview">
        <p style={{ color: "var(--muted)" }}>
          DataPrismAI is a <strong style={{ color: "var(--foreground)" }}>modular GenBI platform</strong> built on a 15-node LangGraph StateGraph pipeline.
          The Next.js frontend communicates with a FastAPI/ASGI backend (port 8010) which orchestrates the agent graph.
          All analytics queries execute on <strong style={{ color: "var(--foreground)" }}>StarRocks</strong> (<code style={{ color: "var(--accent-2)" }}>cc_analytics</code> DB, 50 tables).
          Operational state (sessions, users, audit) lives in <strong style={{ color: "var(--foreground)" }}>PostgreSQL</strong>.
          LLM inference is served locally by <strong style={{ color: "var(--foreground)" }}>Ollama</strong> — no external API calls.
        </p>
      </Section>

      <Section title="LangGraph Pipeline — 15 Nodes">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-3 py-1">#</th>
              <th className="text-left pr-4 py-1">Node</th>
              <th className="text-left py-1">Responsibility</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["1",  "guardrail",          "Classifies query: valid / greeting / off_topic / clarify — blocks invalid early"],
              ["2",  "entity_resolver",    "Extracts entity IDs (customer_id, account_id); rewrites pronoun follow-ups"],
              ["3",  "planner",            "Deterministic intent classification: preview_data · schema_query · metric_query · insight_query · report"],
              ["4",  "persona",            "Loads persona prompt template; scopes metric access by role"],
              ["5",  "semantic_resolver",  "Resolves NL metric → canonical SQL from semantic catalog + dimensions"],
              ["6",  "vanna_sql",          "NL-to-SQL: fast-path patterns → Vanna RAG → Ollama LLM (chat_mode aware)"],
              ["7",  "sql_validator",      "Validates SQL syntax + schema; flags missing tables/columns"],
              ["8",  "query_router",       "Routes to StarRocks or PostgreSQL based on target_engine"],
              ["9",  "query_executor",     "Executes SQL via SQLAlchemy; returns typed result dict"],
              ["10", "result_evaluator",   "Evaluates result quality; triggers retry (max 1×) if poor"],
              ["11", "visualization",      "Recommends chart type (bar/line/pie/scatter/heatmap); builds ECharts config"],
              ["12", "insight",            "Generates NL insights, bottleneck flags, KPI metrics, highlight actions"],
              ["13", "recommendation",     "Produces follow-up questions and insight recommendation list"],
              ["14", "response",           "Assembles the full ChatQueryResponse for the API"],
              ["15", "persist",            "Writes conversation + messages to PostgreSQL store"],
            ].map(([n, node, desc]) => (
              <tr key={node} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-3 py-1 font-mono text-center" style={{ color: "var(--muted)" }}>{n}</td>
                <td className="pr-4 py-1 font-mono text-[11px]" style={{ color: "var(--accent-1)" }}>{node}</td>
                <td className="py-1">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs mt-2" style={{ color: "var(--muted)" }}>
          Conditional edges: <code style={{ color: "var(--accent-2)" }}>guardrail→blocked→persist</code> (early exit) · <code style={{ color: "var(--accent-2)" }}>planner→fast_path→vanna_sql</code> (skip persona+semantic for previews) · <code style={{ color: "var(--accent-2)" }}>result_evaluator→retry→vanna_sql</code> (max 1 retry).
        </p>
      </Section>

      <Section title="NL-to-SQL Strategy (chat_mode)">
        <table className="w-full text-xs border-collapse mt-1">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Mode</th>
              <th className="text-left py-1">Execution path</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["pattern", "direct_table_sql → analytical_pattern_sql → canonical_metric_sql → empty (no LLM)"],
              ["llm",     "_enrich_with_dictionary → Vanna (if ready) → Ollama prompt → parse JSON"],
              ["hybrid",  "direct_table_sql → analytical_pattern_sql → unknown_table_check → canonical_metric_sql → Vanna → Ollama"],
            ].map(([m, p]) => (
              <tr key={m} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-mono" style={{ color: "var(--accent-1)" }}>{m}</td>
                <td className="py-1 font-mono text-[10px]">{p}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Skills Marketplace (5 skills)">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Skill</th>
              <th className="text-left py-1">Purpose</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["nl2sql",            "Convert governed NL questions to SQL using approved semantic context"],
              ["chart-recommender", "Select optimal ECharts chart type + build full config from result rows"],
              ["insight-generator", "Generate NL insights, bottlenecks, and KPI highlights from query results"],
              ["query-router",      "Route queries to the correct engine (StarRocks vs PostgreSQL) by table prefix"],
              ["sql-validator",     "Parse and validate SQL syntax + schema before execution"],
            ].map(([s, d]) => (
              <tr key={s} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-mono text-[11px]" style={{ color: "var(--accent-1)" }}>{s}</td>
                <td className="py-1">{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="API Endpoints">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Method · Path</th>
              <th className="text-left py-1">Purpose</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["POST /chat/query",                        "Main pipeline — runs LangGraph graph (chat_mode, persona, time_range)"],
              ["POST /chat/suggestions",                  "LLM-based follow-up / insight recommendation refresh"],
              ["GET  /semantic/catalog",                  "Full metric catalog — metrics + dimensions (SemanticCatalogResponse)"],
              ["GET  /semantic/tables",                   "Merged live+static 50-table inventory for Data Explorer"],
              ["GET  /semantic/profiling/{table}",        "Per-column profile: null %, distinct, min/max/avg, top values"],
              ["GET  /semantic/sample/{table}",           "Paginated sample rows (offset + limit)"],
              ["GET  /dictionary/tables",                 "Business dictionary table list (45 entries)"],
              ["GET  /dictionary/tables/{name}",          "Full table detail with column definitions"],
              ["GET  /dictionary/columns/{table}",        "Column business descriptions for a table"],
              ["GET  /dictionary/relationships",          "FK relationship graph for ERD rendering"],
              ["GET  /dictionary/search",                 "Full-text search across dictionary"],
              ["GET  /model",                             "List available Ollama models + active model"],
              ["POST /model/switch",                      "Hot-swap active LLM model at runtime"],
              ["GET  /model/status",                      "Ollama health + loaded model status"],
              ["GET  /skills/catalog",                    "Skills marketplace manifest"],
              ["GET  /store/conversations",               "Conversation session history"],
              ["POST /store/conversations",               "Create new conversation session"],
              ["GET  /store/conversations/{id}/messages", "Fetch messages for a conversation"],
              ["POST /store/reports",                     "Save a query result as a report"],
            ].map(([ep, desc]) => (
              <tr key={ep} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-mono text-[10px] whitespace-nowrap" style={{ color: "var(--accent-1)" }}>{ep}</td>
                <td className="py-1">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="SchemaRegistry">
        <p style={{ color: "var(--muted)" }}>
          A thread-safe singleton (<code style={{ color: "var(--accent-2)" }}>registry</code>) loads StarRocks tables from
          {" "}<code style={{ color: "var(--accent-2)" }}>cc_analytics</code> at startup via <code>SHOW TABLES</code>.
          Tables are classified by prefix into 7 layers. A <strong style={{ color: "var(--foreground)" }}>merge strategy</strong> ensures all 50 canonical tables are always available
          (live data overwrites static baseline; offline mode falls back to <code>_STATIC_EXPLORER_TABLES</code>). 30-second retry throttle handles cold-starts.
        </p>
      </Section>

      <Section title="Security">
        <ul className="list-disc ml-4 space-y-1 mt-1" style={{ color: "var(--muted)" }}>
          <li>All SQL is validated (syntax + schema) before execution — read-only enforced by guardrails.</li>
          <li>Persona-scoped prompts restrict which metrics and tables can be surfaced per role.</li>
          <li>Every user action is written to the PostgreSQL audit log (<code>audit_query_log</code>).</li>
          <li>StarRocks + PostgreSQL credentials injected via environment variables — never in source.</li>
          <li>No external LLM API calls — all inference runs locally via Ollama.</li>
        </ul>
      </Section>
    </div>
  );
}

// ── Versions content ───────────────────────────────────────────────────────
function Versions() {
  return (
    <div className="space-y-6 text-sm" style={{ color: "var(--foreground)" }}>
      {COMPONENT_VERSIONS.map(({ category, items }) => (
        <div key={category}>
          <h3 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: "var(--accent-1)" }}>
            {category}
          </h3>
          <table className="w-full border-collapse">
            <thead>
              <tr className="text-xs" style={{ color: "var(--muted)", borderBottom: "1px solid var(--card-border)" }}>
                <th className="text-left pr-6 py-1 font-medium">Component</th>
                <th className="text-left pr-6 py-1 font-medium">Version</th>
                <th className="text-left py-1 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {items.map(({ name, version, description }) => (
                <tr key={name} className="text-xs" style={{ borderBottom: "1px solid var(--card-border)" }}>
                  <td className="pr-6 py-1.5 font-semibold" style={{ color: "var(--foreground)" }}>{name}</td>
                  <td className="pr-6 py-1.5 font-mono" style={{ color: "var(--accent-2)" }}>{version}</td>
                  <td className="py-1.5" style={{ color: "var(--muted)" }}>{description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

// ── Shared section heading ─────────────────────────────────────────────────
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: "var(--accent-1)" }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

// ── Main panel ─────────────────────────────────────────────────────────────
export function HelpPanel() {
  const [activeTab, setActiveTab] = useState<HelpTab>("refarch");

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="shrink-0 px-6 pt-6 pb-0">
        <h1 className="text-lg font-bold tracking-tight" style={{ color: "var(--foreground)" }}>
          Help &amp; Documentation
        </h1>
        <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
          DataPrismAI v{APP_VERSION} — Banking Analytics Platform
        </p>

        {/* Tab bar */}
        <div className="flex gap-1 mt-4" style={{ borderBottom: "1px solid var(--card-border)" }}>
          {TABS.map(({ id, label, icon }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium transition-colors rounded-t"
                style={active
                  ? { color: "var(--accent-1)", borderBottom: "2px solid var(--accent-1)", marginBottom: "-1px", backgroundColor: "var(--panel-bg)" }
                  : { color: "var(--muted)", borderBottom: "2px solid transparent" }}
              >
                <span>{icon}</span>
                <span>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "refarch" ? (
          <iframe
            src="/docs/reference-architecture.html"
            className="w-full h-full border-0"
            title="Reference Architecture"
            sandbox="allow-scripts allow-same-origin"
          />
        ) : (
          <div className="h-full overflow-y-auto px-6 py-6">
            <div className="mx-auto max-w-4xl">
              {activeTab === "userguide" && <UserGuide />}
              {activeTab === "techspec"  && <TechSpec />}
              {activeTab === "versions"  && <Versions />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
