"use client";

import { useState, useEffect } from "react";
import { getAuditLog, clearAuditLog, type AuditEvent, type AuditEventType } from "@/lib/audit";

const TYPE_META: Record<AuditEventType, { label: string; icon: string; color: string }> = {
  login:           { label: "Login",           icon: "🔑", color: "var(--accent-1)" },
  logout:          { label: "Logout",          icon: "🚪", color: "var(--muted)" },
  chat_query:      { label: "Chat Query",      icon: "💬", color: "var(--accent-2)" },
  table_select:    { label: "Table Select",    icon: "🗂",  color: "var(--accent-3)" },
  dataset_change:  { label: "Dataset Change",  icon: "🔄", color: "var(--accent-4)" },
  persona_change:  { label: "Persona Change",  icon: "👤", color: "#a855f7" },
  view_change:     { label: "View Change",     icon: "📐", color: "var(--muted)" },
  report_download: { label: "Download",        icon: "⬇",  color: "#f59e0b" },
  settings_change: { label: "Settings",        icon: "⚙",  color: "var(--muted)" },
};

function formatTs(ts: number) {
  const d = new Date(ts);
  return d.toLocaleString(undefined, { dateStyle: "short", timeStyle: "medium" });
}

export function AuditPanel() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [filter, setFilter] = useState<AuditEventType | "all">("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setEvents(getAuditLog());
    const id = setInterval(() => setEvents(getAuditLog()), 5000);
    return () => clearInterval(id);
  }, []);

  const filtered = events.filter((e) => {
    if (filter !== "all" && e.type !== filter) return false;
    if (search && !e.detail.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  function handleClear() {
    if (confirm("Clear all audit logs? This cannot be undone.")) {
      clearAuditLog();
      setEvents([]);
    }
  }

  function exportCSV() {
    const rows = [
      ["Timestamp", "Type", "User", "Detail"],
      ...filtered.map((e) => [
        new Date(e.ts).toISOString(),
        e.type,
        e.userName ?? "",
        `"${e.detail.replace(/"/g, '""')}"`,
      ]),
    ];
    const csv = rows.map((r) => r.join(",")).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `dataprismai-audit-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold" style={{ fontFamily: "var(--font-display)", color: "var(--foreground)" }}>
            Audit Log
          </h2>
          <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
            All user activities tracked in real time · {events.length} total events
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportCSV}
            className="rounded-xl px-3 py-1.5 text-xs font-medium transition-opacity hover:opacity-80"
            style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--tag-bg)", color: "var(--foreground)" }}
          >
            ⬇ Export CSV
          </button>
          <button
            onClick={handleClear}
            className="rounded-xl px-3 py-1.5 text-xs font-medium"
            style={{ border: "1px solid rgba(239,68,68,0.4)", color: "#ef4444", backgroundColor: "rgba(239,68,68,0.06)" }}
          >
            🗑 Clear
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search events…"
          className="rounded-xl px-3 py-1.5 text-xs outline-none min-w-48"
          style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--panel-bg)", color: "var(--foreground)" }}
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as AuditEventType | "all")}
          className="rounded-xl px-3 py-1.5 text-xs cursor-pointer"
          style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--panel-bg)", color: "var(--foreground)" }}
        >
          <option value="all">All Types</option>
          {Object.entries(TYPE_META).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
        <div className="text-xs self-center" style={{ color: "var(--muted)" }}>
          {filtered.length} events
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
        {(Object.entries(TYPE_META) as [AuditEventType, typeof TYPE_META[AuditEventType]][]).map(([k, v]) => {
          const count = events.filter((e) => e.type === k).length;
          if (!count) return null;
          return (
            <div
              key={k}
              className="rounded-xl p-2.5 text-center"
              style={{ backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}
            >
              <div className="text-lg">{v.icon}</div>
              <div className="text-base font-bold" style={{ color: v.color, fontFamily: "var(--font-display)" }}>{count}</div>
              <div className="text-[10px]" style={{ color: "var(--muted)" }}>{v.label}</div>
            </div>
          );
        })}
      </div>

      {/* Event table */}
      {filtered.length === 0 ? (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}
        >
          <div className="text-2xl mb-2">📋</div>
          <div className="text-sm" style={{ color: "var(--muted)" }}>No audit events yet. Start using the app to generate activity.</div>
        </div>
      ) : (
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
          <div style={{ backgroundColor: "var(--panel-bg)", borderBottom: "1px solid var(--card-border)" }}
            className="grid grid-cols-12 px-4 py-2 text-[10px] font-bold uppercase tracking-widest">
            <div className="col-span-3" style={{ color: "var(--muted)" }}>Timestamp</div>
            <div className="col-span-2" style={{ color: "var(--muted)" }}>Type</div>
            <div className="col-span-2" style={{ color: "var(--muted)" }}>User</div>
            <div className="col-span-5" style={{ color: "var(--muted)" }}>Detail</div>
          </div>
          <div className="max-h-[500px] overflow-y-auto">
            {filtered.map((e, i) => {
              const meta = TYPE_META[e.type];
              return (
                <div
                  key={e.id}
                  className="grid grid-cols-12 px-4 py-2.5 text-xs items-start"
                  style={{
                    backgroundColor: i % 2 === 0 ? "var(--card-bg)" : "var(--panel-bg)",
                    borderBottom: "1px solid var(--card-border)",
                  }}
                >
                  <div className="col-span-3" style={{ color: "var(--muted)", fontFamily: "var(--font-mono)" }}>
                    {formatTs(e.ts)}
                  </div>
                  <div className="col-span-2 flex items-center gap-1.5">
                    <span>{meta.icon}</span>
                    <span style={{ color: meta.color }}>{meta.label}</span>
                  </div>
                  <div className="col-span-2" style={{ color: "var(--foreground)" }}>
                    {e.userName ?? "—"}
                  </div>
                  <div className="col-span-5 leading-relaxed" style={{ color: "var(--foreground)" }}>
                    {e.detail}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
