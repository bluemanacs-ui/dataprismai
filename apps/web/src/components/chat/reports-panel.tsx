"use client";

import { useState } from "react";
import { ChatMessage } from "@/types/chat";
import { InlineChartCard } from "./inline-chart-card";

type ReportsPanelProps = {
  reports: ChatMessage[];
};

// ── Canned reports ─────────────────────────────────────────────────────────────
const CANNED_REPORTS = [
  {
    id: "spend_monthly",
    title: "Monthly Spend Trend",
    description: "Total card spend grouped by month over the last 24 months.",
    icon: "📈",
    domain: "Revenue",
    query: "Show total spend by month",
  },
  {
    id: "fraud_by_merchant",
    title: "Fraud Rate by Merchant",
    description: "Fraud rate percentage broken down by merchant category code.",
    icon: "🛡",
    domain: "Risk",
    query: "Show fraud rate by merchant category",
  },
  {
    id: "delinquency_status",
    title: "Delinquency by Account Status",
    description: "Delinquent accounts grouped by current account status.",
    icon: "⚠️",
    domain: "Credit Risk",
    query: "Show delinquency rate by account status",
  },
  {
    id: "payment_volume",
    title: "Payment Volume Trend",
    description: "Total payment amounts and payment count over time.",
    icon: "💳",
    domain: "Payments",
    query: "Show payment volume by month",
  },
  {
    id: "credit_score_dist",
    title: "Credit Score Distribution",
    description: "Customer credit scores grouped by income band.",
    icon: "📊",
    domain: "Credit",
    query: "Show customer credit score by income band",
  },
  {
    id: "top_customers",
    title: "Top Customers by Cards",
    description: "Customers with the highest number of active cards.",
    icon: "👥",
    domain: "Portfolio",
    query: "List customers with highest number of cards",
  },
];

const SUPERSET_URL = process.env.NEXT_PUBLIC_SUPERSET_URL ?? "http://localhost:8088";

type TabId = "canned" | "history" | "superset";

function TabBtn({
  id,
  label,
  activeTab,
  setActiveTab,
}: {
  id: TabId;
  label: string;
  activeTab: TabId;
  setActiveTab: (t: TabId) => void;
}) {
  return (
    <button
      onClick={() => setActiveTab(id)}
      className="rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
    style={activeTab === id
        ? { backgroundColor: "var(--accent-1)", color: "white" }
        : { color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}
    >
      {label}
    </button>
  );
}

// ── Superset embed section ─────────────────────────────────────────────────────
function SupersetSection() {
  const [tab, setTab] = useState<"link" | "embed">("link");
  return (
    <div className="rounded-2xl p-4" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Apache Superset BI</div>
          <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>Connect to your Superset instance for advanced dashboards</div>
        </div>
        <div className="flex gap-1">
          <button onClick={() => setTab("link")}
            className="rounded px-2 py-1 text-[10px]"
            style={tab === "link" ? { backgroundColor: "var(--accent-2)", color: "white" } : { color: "var(--muted)" }}>
            Link
          </button>
          <button onClick={() => setTab("embed")}
            className="rounded px-2 py-1 text-[10px]"
            style={tab === "embed" ? { backgroundColor: "var(--accent-2)", color: "white" } : { color: "var(--muted)" }}>
            Embed
          </button>
        </div>
      </div>
      {tab === "link" ? (
        <div className="space-y-2">
          <a href={SUPERSET_URL} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-xl px-4 py-3 transition-colors"
            style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
            <span className="text-xl">📊</span>
            <div>
              <div className="text-sm font-medium" style={{ color: "var(--foreground)" }}>Open Superset Dashboard</div>
              <div className="text-[10px] font-mono" style={{ color: "var(--muted)" }}>{SUPERSET_URL}</div>
            </div>
            <span className="ml-auto text-xs" style={{ color: "var(--muted)" }}>↗</span>
          </a>
          <div className="text-[10px] px-1" style={{ color: "var(--muted)" }}>
            Set <code style={{ color: "var(--accent-3)" }}>NEXT_PUBLIC_SUPERSET_URL</code> in .env to point to your Superset instance.
          </div>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl" style={{ border: "1px solid var(--card-border)" }}>
          <iframe
            src={`${SUPERSET_URL}/superset/welcome`}
            className="h-120 w-full"
            title="Superset BI"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </div>
      )}
    </div>
  );
}

// ── Main ReportsPanel ──────────────────────────────────────────────────────────
export function ReportsPanel({ reports }: ReportsPanelProps) {
  const [activeReport, setActiveReport] = useState<ChatMessage | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>("canned");

  return (
    <div className="space-y-4">
      {/* Header with tabs */}
      <div className="rounded-2xl p-4" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
        <div className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>Reports</div>
        <div className="mt-0.5 text-xs" style={{ color: "var(--muted)" }}>Canned analytics, query history, and BI integration</div>
        <div className="mt-3 flex gap-1">
          <TabBtn id="canned" label="📋 Canned Reports" activeTab={activeTab} setActiveTab={setActiveTab} />
          <TabBtn id="history" label={`📁 History (${reports.length})`} activeTab={activeTab} setActiveTab={setActiveTab} />
          <TabBtn id="superset" label="📊 Superset BI" activeTab={activeTab} setActiveTab={setActiveTab} />
        </div>
      </div>

      {/* Canned reports tab */}
      {activeTab === "canned" && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CANNED_REPORTS.map(r => (
            <div key={r.id}
              className="rounded-2xl p-4 flex flex-col gap-3 cursor-pointer transition-all hover:opacity-90"
              style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
              <div className="flex items-start gap-3">
                <span className="text-2xl">{r.icon}</span>
                <div>
                  <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>{r.title}</div>
                  <div className="text-[10px] mt-0.5" style={{ color: "var(--accent-2)" }}>{r.domain}</div>
                </div>
              </div>
              <div className="text-xs flex-1" style={{ color: "var(--muted)" }}>{r.description}</div>
              <a href={`/?q=${encodeURIComponent(r.query)}`}
                onClick={e => { e.preventDefault(); window.dispatchEvent(new CustomEvent("dataprismai:query", { detail: r.query })); }}
                className="mt-auto rounded-lg px-3 py-2 text-center text-xs font-medium transition-colors"
                style={{ backgroundColor: "var(--accent-1)", color: "white" }}>
                Run Report
              </a>
            </div>
          ))}
        </div>
      )}

      {/* History tab */}
      {activeTab === "history" && (
        reports.length === 0 ? (
          <div className="rounded-2xl p-8 text-center space-y-2" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
            <div className="text-2xl">📁</div>
            <div className="text-sm" style={{ color: "var(--muted)" }}>No reports yet</div>
            <div className="text-xs" style={{ color: "var(--muted)" }}>Every query that returns data is saved here.</div>
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {reports.map(report => {
              const isActive = activeReport?.id === report.id;
              const metric = report.semanticContext?.metric ?? "Analysis";
              const rowCount = report.resultRowCount ?? 0;
              const engine = report.resultEngine ?? "";
              const execTime = report.resultExecutionTimeMs ?? 0;
              return (
                <div key={report.id}
                  className="rounded-2xl p-4 cursor-pointer transition-all"
                  style={{
                    border: isActive ? "1px solid var(--accent-2)" : "1px solid var(--card-border)",
                    backgroundColor: "var(--card-bg)",
                    boxShadow: isActive ? "0 0 0 2px rgba(26,111,224,0.2)" : undefined,
                  }}
                  onClick={() => setActiveReport(isActive ? null : report)}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>{metric}</div>
                      <div className="text-xs mt-0.5 line-clamp-2" style={{ color: "var(--muted)" }}>{report.content}</div>
                    </div>
                    <span className="shrink-0 rounded px-2 py-0.5 text-[10px]" style={{ backgroundColor: "rgba(26,111,224,0.15)", color: "var(--accent-2)" }}>
                      {rowCount} rows
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px]" style={{ color: "var(--muted)" }}>
                    {engine && <span>Engine: {engine}</span>}
                    {execTime > 0 && <span>{execTime}ms</span>}
                    {(report.insights ?? []).length > 0 && (
                      <span>{(report.insights ?? []).length} insight{(report.insights ?? []).length !== 1 ? "s" : ""}</span>
                    )}
                  </div>
                  {isActive && (
                    <div className="mt-4 pt-4 space-y-3" style={{ borderTop: "1px solid var(--card-border)" }}>
                      {(report.insights ?? []).length > 0 && (
                        <div>
                          <div className="text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>Key Insights</div>
                          <ul className="space-y-1">
                            {(report.insights ?? []).map((ins, i) => (
                              <li key={i} className="text-xs" style={{ color: "var(--foreground)" }}>• {ins}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {report.sql && (
                        <details className="text-xs">
                          <summary className="cursor-pointer" style={{ color: "var(--muted)" }}>View SQL</summary>
                          <pre className="mt-2 overflow-x-auto rounded-lg p-3 text-[10px] leading-relaxed whitespace-pre-wrap" style={{ backgroundColor: "var(--step-bg)", color: "var(--foreground)" }}>
                            {report.sql}
                          </pre>
                        </details>
                      )}
                      {report.chartConfig && (
                        <InlineChartCard chartConfig={report.chartConfig} />
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )
      )}

      {/* Superset tab */}
      {activeTab === "superset" && <SupersetSection />}
    </div>
  );
}


