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
const APP_VERSION = "0.1.0";

const COMPONENT_VERSIONS: { category: string; items: { name: string; version: string; description: string }[] }[] = [
  {
    category: "Application",
    items: [
      { name: "DataPrismAI",   version: APP_VERSION, description: "Banking analytics platform" },
    ],
  },
  {
    category: "Frontend",
    items: [
      { name: "Next.js",     version: "16.2.2", description: "React full-stack framework" },
      { name: "React",       version: "19.2.4", description: "UI component library" },
      { name: "TypeScript",  version: "5.x",    description: "Typed JavaScript superset" },
      { name: "Tailwind CSS",version: "4.x",    description: "Utility-first CSS framework" },
      { name: "ECharts",     version: "6.0.0",  description: "Data visualisation (charts)" },
      { name: "ReactFlow",   version: "12.10.2",description: "Node-graph visualisation" },
    ],
  },
  {
    category: "Backend / API",
    items: [
      { name: "FastAPI",     version: "0.135.3", description: "Python async REST framework" },
      { name: "Uvicorn",     version: "0.42.0",  description: "ASGI web server" },
      { name: "Python",      version: "3.12",    description: "Runtime" },
      { name: "LangGraph",   version: "1.1.5",   description: "Stateful agent graph runtime" },
      { name: "LangChain Core", version: "1.2.25", description: "LLM interaction primitives" },
      { name: "Vanna",       version: "2.0.2",   description: "NL-to-SQL generation engine" },
      { name: "Alembic",     version: "1.18.4",  description: "Database migration tool" },
    ],
  },
  {
    category: "AI / LLM",
    items: [
      { name: "Ollama",         version: "—",           description: "Local LLM runtime" },
      { name: "qwen2.5:7b",     version: "7B params",   description: "Primary inference model" },
    ],
  },
  {
    category: "Data Layer",
    items: [
      { name: "StarRocks",   version: "3.x",    description: "MPP analytics engine (cc_analytics DB)" },
      { name: "PostgreSQL",  version: "15.x",   description: "Operational store (sessions, users)" },
      { name: "Trino",       version: "—",      description: "Federated query engine (optional)" },
    ],
  },
];

// ── User Guide content ─────────────────────────────────────────────────────
function UserGuide() {
  return (
    <div className="prose max-w-none space-y-6 text-sm" style={{ color: "var(--foreground)" }}>
      <Section title="Getting Started">
        <p>DataPrismAI lets you query your banking data using plain English. Sign in, select your workspace persona, and type a question in the chat panel.</p>
        <ol className="list-decimal ml-4 space-y-1 mt-2">
          <li>Log in with your platform credentials.</li>
          <li>Your persona (Fraud Analyst, Finance User, Analyst, etc.) is set by your role.</li>
          <li>Type a question like <em>&ldquo;Show top 10 transactions this week&rdquo;</em> and press Enter.</li>
          <li>DataPrismAI generates SQL, queries StarRocks, and returns a rich answer card.</li>
        </ol>
      </Section>
      <Section title="Chat Interface">
        <ul className="list-disc ml-4 space-y-1">
          <li><strong>Ask anything</strong> — the AI maps natural language to SQL automatically.</li>
          <li><strong>Insight Recommendations</strong> — each answer card suggests related deep-dives. Click or hit ↺ to refresh for more.</li>
          <li><strong>Follow-up Questions</strong> — quick-action suggestions appear below every answer to help you drill down.</li>
          <li><strong>SQL &amp; Reasoning</strong> — expand <em>Details</em> on any answer card to see the generated SQL, semantic context, and chain-of-thought reasoning.</li>
          <li><strong>Charts</strong> — qualifying results are automatically visualised as bar, line, or pie charts.</li>
        </ul>
      </Section>
      <Section title="Data Explorer">
        <p>Navigate to <strong>Data Explorer</strong> in the sidebar to browse the metric catalog, view table schemas, and inspect data products. Click any metric to auto-generate a query.</p>
      </Section>
      <Section title="Reports">
        <p>All successful query results are stored under <strong>Reports</strong>. Re-run a saved report by clicking its card or start a canned report from the report templates.</p>
      </Section>
      <Section title="Audit">
        <p>The <strong>Audit</strong> panel records every query, login, and navigation event for your session. Administrators can review the full audit trail for compliance.</p>
      </Section>
      <Section title="Settings">
        <p>Switch between <strong>Dark</strong> and <strong>Light (Dawn)</strong> themes from the top-bar toggle or the Settings panel. Additional profile options are available in Settings.</p>
      </Section>
      <Section title="Personas Explained">
        <table className="w-full text-xs border-collapse mt-2">
          <thead>
            <tr style={{ color: "var(--accent-1)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Persona</th>
              <th className="text-left pr-4 py-1">Focus</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["Fraud Analyst",        "Suspicious transactions, fraud rates, alert trends"],
              ["Finance User",         "Portfolio KPIs, delinquency, P&L, MTD vs prior period"],
              ["Regional Finance",     "Country-level KPIs, regional benchmarking"],
              ["Regional Risk",        "Cross-region fraud and delinquency heat maps"],
              ["Retail User",          "Customer spend, payment status, segment breakdowns"],
              ["Analyst (default)",    "General exploration — all metrics accessible"],
            ].map(([p, f]) => (
              <tr key={p} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-medium" style={{ color: "var(--foreground)" }}>{p}</td>
                <td className="py-1">{f}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tech Spec content ──────────────────────────────────────────────────────
function TechSpec() {
  return (
    <div className="space-y-6 text-sm" style={{ color: "var(--foreground)" }}>
      <Section title="Architecture Overview">
        <p style={{ color: "var(--muted)" }}>
          DataPrismAI follows a <strong style={{ color: "var(--foreground)" }}>modular multi-agent architecture</strong> built on a 13-node LangGraph pipeline.
          The frontend (Next.js) communicates with a FastAPI backend that orchestrates the graph.
          All analytics queries are executed against StarRocks; operational state lives in PostgreSQL.
        </p>
      </Section>
      <Section title="LangGraph Pipeline (13 nodes)">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">#</th>
              <th className="text-left pr-4 py-1">Node</th>
              <th className="text-left py-1">Responsibility</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["1",  "guardrail_node",       "Validates query — valid / greeting / off_topic / clarify"],
              ["2",  "persona_node",         "Loads persona prompt template and context"],
              ["3",  "planner_node",         "Classifies intent + extracts literal table name"],
              ["4",  "semantic_resolver",    "Resolves metric → semantic context from catalog"],
              ["5",  "entity_resolver",      "Extracts entity IDs (customer, account) from message"],
              ["6",  "vanna_sql_node",       "Fast-path SQL for preview/schema; Vanna NL-to-SQL otherwise"],
              ["7",  "sql_validation_node",  "Validates generated SQL (syntax + schema)"],
              ["8",  "query_executor_node",  "Executes SQL on StarRocks via SQLAlchemy"],
              ["9",  "result_evaluator",     "Evaluates quality; triggers retry if needed"],
              ["10", "insight_node",         "Generates natural-language insights from results"],
              ["11", "recommendation_node",  "Produces follow-ups and insight recommendations"],
              ["12", "chart_node",           "Recommends and configures ECharts visualisation"],
              ["13", "response_node",        "Formats final ChatQueryResponse for the API"],
            ].map(([n, node, desc]) => (
              <tr key={node} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-mono" style={{ color: "var(--muted)" }}>{n}</td>
                <td className="pr-4 py-1 font-mono text-[11px]" style={{ color: "var(--accent-1)" }}>{node}</td>
                <td className="py-1">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Section title="SchemaRegistry">
        <p style={{ color: "var(--muted)" }}>
          A thread-safe singleton (<code style={{ color: "var(--accent-2)" }}>registry</code>) loads all StarRocks tables from{" "}
          <code style={{ color: "var(--accent-2)" }}>cc_analytics</code> at startup via <code>SHOW TABLES</code>.
          Tables are categorised (<em>raw</em>, <em>semantic</em>, <em>mapping</em>, <em>dp</em>, <em>ddm</em>, <em>audit</em>).
          All pipeline nodes use the registry as the exclusive source of truth; a 30-second retry throttle handles cold-starts.
        </p>
      </Section>
      <Section title="NL-to-SQL Strategy">
        <ul className="list-disc ml-4 space-y-1 mt-1" style={{ color: "var(--muted)" }}>
          <li><strong style={{ color: "var(--foreground)" }}>Vanna (primary)</strong> — RAG-augmented NL-to-SQL trained on StarRocks DDL and sample queries.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Deterministic fast-path</strong> — <code>preview_data</code> and <code>schema_query</code> intents bypass LLM entirely with hand-crafted SQL templates.</li>
          <li><strong style={{ color: "var(--foreground)" }}>Retry loop</strong> — <code>result_evaluator→vanna_sql</code> conditional edge retries up to 2× when result quality is poor.</li>
        </ul>
      </Section>
      <Section title="API Endpoints">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr style={{ color: "var(--accent-2)", borderBottom: "1px solid var(--card-border)" }}>
              <th className="text-left pr-4 py-1">Method + Path</th>
              <th className="text-left py-1">Purpose</th>
            </tr>
          </thead>
          <tbody style={{ color: "var(--muted)" }}>
            {[
              ["POST /chat/query",          "Main pipeline — runs LangGraph graph"],
              ["POST /chat/suggestions",    "LLM-based follow-up / recommendation refresh"],
              ["GET  /semantic/catalog",    "Full metric catalog (metrics + dimensions)"],
              ["GET  /semantic/tables",     "StarRocks table list for Data Explorer"],
              ["GET  /skills",              "Skills marketplace manifest"],
              ["GET  /api/store/sessions",  "Conversation session history"],
              ["GET  /langgraph/status",    "Graph health check"],
            ].map(([ep, desc]) => (
              <tr key={ep} style={{ borderBottom: "1px solid var(--card-border)" }}>
                <td className="pr-4 py-1 font-mono text-[11px]" style={{ color: "var(--accent-1)" }}>{ep}</td>
                <td className="py-1">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Section title="Security Notes">
        <ul className="list-disc ml-4 space-y-1 mt-1" style={{ color: "var(--muted)" }}>
          <li>All SQL is parameterised or validated before execution.</li>
          <li>Persona-scoped prompts restrict what data can be surfaced per role.</li>
          <li>Every user action is written to the audit log (PostgreSQL).</li>
          <li>StarRocks credentials are injected via environment variables — never stored in code.</li>
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
