"use client";

import { useState } from "react";
import { DEMO_USERS, ROLE_LABEL, ROLE_PERSONA_MAP, type AppUser, type UserRole } from "@/lib/auth";

const ROLE_DESC: Record<string, string> = {
  admin:                  "Full platform access across all domains and countries",
  fraud_analyst:          "Risk + transaction-level investigation and fraud detection",
  retail_user:            "Spend, payments, and customer-level retail card operations",
  finance_user:           "Portfolio KPIs, spend roll-ups, executive P&L view",
  regional_finance_user:  "Regional P&L and portfolio KPIs scoped to country/entity",
  regional_risk_user:     "Country-scoped risk metrics and transaction monitoring",
};

// Domain pill colors (same as login panel)
const DOMAIN_COLORS: Record<string, string> = {
  risk:        "#ef4444",
  transactions:"#f59e0b",
  customer:    "#3b82f6",
  spend:       "#8b5cf6",
  payments:    "#06b6d4",
  portfolio:   "#10b981",
};

type SettingsPanelProps = {
  currentUser?: AppUser;
  onThemeChange?: (t: "dark" | "dawn") => void;
  currentTheme?: "dark" | "dawn";
};

export function SettingsPanel({ currentUser, onThemeChange, currentTheme = "dark" }: SettingsPanelProps) {
  const [tab, setTab] = useState<"profile" | "users" | "roles" | "system">("profile");

  const tabs = [
    { id: "profile" as const, label: "Profile", icon: "👤" },
    { id: "users" as const,   label: "Users",   icon: "🧑‍💼" },
    { id: "roles" as const,   label: "Roles",   icon: "🔐" },
    { id: "system" as const,  label: "System",  icon: "⚙" },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold" style={{ fontFamily: "var(--font-display)", color: "var(--foreground)" }}>
          Settings
        </h2>
        <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
          Platform configuration, user management and preferences
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 rounded-xl p-1" style={{ backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}>
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex-1 rounded-lg px-3 py-2 text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
            style={tab === t.id
              ? { backgroundColor: "var(--accent-1)", color: "white" }
              : { color: "var(--muted)" }}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* Profile */}
      {tab === "profile" && currentUser && (
        <div className="rounded-2xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <div className="flex items-start gap-4">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-full text-lg font-bold"
              style={{ backgroundColor: "var(--accent-1)", color: "white" }}
            >
              {currentUser.name.charAt(0)}
            </div>
            <div>
              <div className="font-semibold text-sm" style={{ color: "var(--foreground)" }}>{currentUser.name}</div>
              <div className="text-xs" style={{ color: "var(--muted)" }}>{currentUser.email}</div>
              <div
                className="mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold"
                style={{ backgroundColor: "rgba(0,165,81,0.12)", color: "var(--accent-1)", border: "1px solid rgba(0,165,81,0.3)" }}
              >
                {ROLE_LABEL[currentUser.role] ?? currentUser.role}
              </div>
            </div>
          </div>
          <div className="mt-4 space-y-2 text-xs" style={{ color: "var(--muted)" }}>
            <div><strong style={{ color: "var(--foreground)" }}>Persona:</strong> {currentUser.persona}</div>
            <div><strong style={{ color: "var(--foreground)" }}>Department:</strong> {currentUser.department}</div>
            <div><strong style={{ color: "var(--foreground)" }}>Default Domain:</strong> {currentUser.default_domain}</div>
            <div><strong style={{ color: "var(--foreground)" }}>Countries:</strong> {currentUser.country_codes.join(", ")}</div>
            <div className="flex flex-wrap gap-1 items-center">
              <strong style={{ color: "var(--foreground)" }}>Domains:</strong>
              {currentUser.allowed_domains.map(d => (
                <span key={d} className="rounded px-1.5 py-0.5 text-[10px]"
                  style={{ backgroundColor: `${DOMAIN_COLORS[d] ?? "#888"}20`, color: DOMAIN_COLORS[d] ?? "var(--muted)" }}>
                  {d}
                </span>
              ))}
            </div>
            <div><strong style={{ color: "var(--foreground)" }}>Role Description:</strong> {ROLE_DESC[currentUser.role] ?? ""}</div>
          </div>
          <div className="mt-5 pt-4" style={{ borderTop: "1px solid var(--card-border)" }}>
            <div className="text-xs font-semibold mb-2" style={{ color: "var(--foreground)" }}>Display Theme</div>
            <div className="flex gap-2">
              {(["dark", "dawn"] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => onThemeChange?.(t)}
                  className="rounded-xl px-4 py-2 text-xs font-medium transition-all"
                  style={currentTheme === t
                    ? { backgroundColor: "var(--accent-2)", color: "white" }
                    : { border: "1px solid var(--card-border)", backgroundColor: "var(--panel-bg)", color: "var(--foreground)" }}
                >
                  {t === "dark" ? "☾ Dark" : "☀ Light"}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Users */}
      {tab === "users" && (
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
          <div style={{ backgroundColor: "var(--panel-bg)", borderBottom: "1px solid var(--card-border)" }}
            className="grid grid-cols-12 px-4 py-2 text-[10px] font-bold uppercase tracking-widest">
            <div className="col-span-3" style={{ color: "var(--muted)" }}>Name</div>
            <div className="col-span-4" style={{ color: "var(--muted)" }}>Email</div>
            <div className="col-span-3" style={{ color: "var(--muted)" }}>Role</div>
            <div className="col-span-2" style={{ color: "var(--muted)" }}>Persona</div>
          </div>
          {DEMO_USERS.map((u, i) => (
            <div
              key={u.id}
              className="grid grid-cols-12 items-center px-4 py-3 text-xs"
              style={{ backgroundColor: i % 2 === 0 ? "var(--card-bg)" : "var(--panel-bg)", borderBottom: "1px solid var(--card-border)" }}
            >
              <div className="col-span-3 flex items-center gap-2">
                <span
                  className="inline-flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold"
                  style={{ backgroundColor: u.id === currentUser?.id ? "var(--accent-1)" : "var(--tag-bg)", color: u.id === currentUser?.id ? "white" : "var(--muted)" }}
                >
                  {u.name.charAt(0)}
                </span>
                <span style={{ color: "var(--foreground)" }}>{u.name}</span>
              </div>
              <div className="col-span-4" style={{ color: "var(--muted)", fontFamily: "var(--font-mono)" }}>{u.email}</div>
              <div className="col-span-3">
                <span className="rounded-full px-2 py-0.5 text-[10px]" style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-3)" }}>
                  {ROLE_LABEL[u.role as UserRole] ?? u.role}
                </span>
              </div>
              <div className="col-span-2" style={{ color: "var(--muted)" }}>{u.persona}</div>
            </div>
          ))}
        </div>
      )}

      {/* Roles */}
      {tab === "roles" && (
        <div className="space-y-3">
          {(Object.entries(ROLE_DESC) as [string, string][]).map(([role, desc]) => (
            <div
              key={role}
              className="rounded-xl p-4"
              style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>{ROLE_LABEL[role as UserRole] ?? role}</span>
                <span className="text-[10px] rounded-full px-2 py-0.5" style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-2)" }}>
                  persona: {ROLE_PERSONA_MAP[role as UserRole] ?? role}
                </span>
              </div>
              <div className="text-xs" style={{ color: "var(--muted)" }}>{desc}</div>
            </div>
          ))}
        </div>
      )}

      {/* System */}
      {tab === "system" && (
        <div className="space-y-3">
          <div className="rounded-2xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
            <div className="text-sm font-semibold mb-3" style={{ color: "var(--foreground)" }}>Platform Configuration</div>
            <div className="space-y-3 text-xs">
              {[
                ["API Base URL", process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api"],
                ["LLM Model", "qwen2.5:7b (Ollama)"],
                ["Query Engine", "StarRocks"],
                ["Metadata Store", "PostgreSQL"],
                ["Version", "DataPrismAI v1.0.0"],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between items-center py-2" style={{ borderBottom: "1px solid var(--card-border)" }}>
                  <span style={{ color: "var(--muted)" }}>{k}</span>
                  <span style={{ color: "var(--foreground)", fontFamily: "var(--font-mono)" }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


