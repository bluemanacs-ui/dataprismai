"use client";

import { useState } from "react";

type ActiveView = "chat" | "explorer" | "reports" | "audit" | "settings" | "help";

type SidebarProps = {
  activeView: ActiveView;
  onChangeView: (view: ActiveView) => void;
  isOpen: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  queryHistory?: { query: string; metric: string; rowCount: number; ts: number }[];
  onHistoryQuery?: (q: string) => void;
  workspaceName?: string;
  persona?: string;
};

const navItems: { label: string; view: ActiveView; icon: string }[] = [
  { label: "Chat",          view: "chat",     icon: "💬" },
  { label: "Data Explorer", view: "explorer", icon: "🔍" },
  { label: "Reports",       view: "reports",  icon: "📊" },
  { label: "Audit",         view: "audit",    icon: "📋" },
  { label: "Settings",      view: "settings", icon: "⚙" },
  { label: "Help",          view: "help",     icon: "❓" },
];

export function Sidebar({
  activeView, onChangeView, isOpen, onToggle,
  onNewChat, queryHistory = [], onHistoryQuery,
  workspaceName, persona,
}: SidebarProps) {
  const [historyExpanded, setHistoryExpanded] = useState(false);

  return (
    <aside
      className={`flex flex-col shrink-0 transition-all duration-200 ${isOpen ? "w-56" : "w-12"}`}
      style={{ borderRight: "1px solid var(--card-border)", backgroundColor: "var(--panel-bg)", color: "var(--foreground)" }}
    >
      {/* Header */}
      <div
        className={`flex h-13 shrink-0 items-center border-b ${isOpen ? "justify-between px-3" : "justify-center"}`}
        style={{ borderColor: "var(--card-border)" }}
      >
        {isOpen && (
          <div className="min-w-0 overflow-hidden">
            <div className="text-[10px] font-bold uppercase tracking-widest truncate" style={{ color: "var(--accent-1)", fontFamily: "var(--font-display)" }}>
              {workspaceName ?? "Workspace"}
            </div>
            {persona && (
              <div className="text-[9px] truncate capitalize" style={{ color: "var(--muted)" }}>{persona}</div>
            )}
          </div>
        )}
        <button
          onClick={onToggle}
          className="rounded p-1 text-xs shrink-0"
          style={{ color: "var(--muted)" }}
          title={isOpen ? "Collapse" : "Expand"}
        >
          {isOpen ? "◀" : "▶"}
        </button>
      </div>

      {/* Collapsed: icon-only */}
      {!isOpen && (
        <div className="mt-2 flex flex-col items-center gap-1 px-1">
          <button onClick={onNewChat} title="New Chat"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-sm"
            style={{ color: "var(--accent-1)" }}>
            ✏️
          </button>
          {navItems.map(({ label, view, icon }) => (
            <button key={view} onClick={() => onChangeView(view)} title={label}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-sm transition-colors"
              style={activeView === view
                ? { backgroundColor: "var(--accent-1)", color: "white" }
                : { color: "var(--muted)" }}>
              {icon}
            </button>
          ))}
        </div>
      )}

      {/* Expanded */}
      {isOpen && (
        <div className="flex flex-1 flex-col overflow-y-auto py-3 px-2.5 gap-3">
          {/* New Chat */}
          <button onClick={onNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold transition-opacity hover:opacity-90"
            style={{ backgroundColor: "var(--accent-1)", color: "white" }}>
            ✏ New Chat
          </button>

          {/* ── Navigation ─────────────────────────────── */}
          <div>
            <div className="mb-1 px-1 text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--muted)" }}>
              Navigation
            </div>
            <div className="space-y-0.5">
              {navItems.map(({ label, view, icon }) => {
                const active = activeView === view;
                return (
                  <button key={view} onClick={() => onChangeView(view)}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-all"
                    style={active
                      ? { backgroundColor: "var(--nav-active-bg)", color: "var(--accent-1)", fontWeight: 600, borderLeft: "3px solid var(--accent-1)" }
                      : { color: "var(--foreground)", borderLeft: "3px solid transparent" }}>
                    <span>{icon}</span> {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Query History ───────────────────────────── */}
          {queryHistory.length > 0 && (
            <div style={{ borderTop: "1px solid var(--card-border)" }} className="pt-3">
              <button
                onClick={() => setHistoryExpanded(v => !v)}
                className="flex w-full items-center justify-between px-1 mb-1.5"
              >
                <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--muted)" }}>
                  Recent Queries
                </span>
                <span className="text-[10px]" style={{ color: "var(--muted)" }}>{historyExpanded ? "▲" : "▼"}</span>
              </button>
              {historyExpanded && (
                <div className="space-y-1">
                  {queryHistory.slice(0, 10).map((h, i) => (
                    <button
                      key={i}
                      onClick={() => onHistoryQuery?.(h.query)}
                      title={h.query}
                      className="flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left text-[11px] transition-colors hover:opacity-80"
                      style={{ color: "var(--foreground)", backgroundColor: "var(--tag-bg)", border: "1px solid var(--card-border)" }}
                    >
                      <span style={{ color: "var(--muted)" }} className="shrink-0">↺</span>
                      <span className="truncate leading-snug">{h.query}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}

export type { ActiveView };
