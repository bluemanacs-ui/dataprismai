"use client";

import { useState } from "react";
import { login, DEMO_USERS, ROLE_LABEL, type AppUser } from "@/lib/auth";

type LoginPanelProps = {
  onLogin: (user: AppUser) => void;
};

// Domain pill colors
const DOMAIN_COLORS: Record<string, string> = {
  risk:        "#ef4444",
  transactions:"#f59e0b",
  customer:    "#3b82f6",
  spend:       "#8b5cf6",
  payments:    "#06b6d4",
  portfolio:   "#10b981",
};

// Persona badge colors (matches semantic_access_control personas)
const PERSONA_COLORS: Record<string, string> = {
  fraud_analyst:         "#ef4444",
  retail_user:           "#8b5cf6",
  finance_user:          "#10b981",
  regional_finance_user: "#06b6d4",
  regional_risk_user:    "#f59e0b",
};

export function LoginPanel({ onLogin }: LoginPanelProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setTimeout(() => {
      const user = login(email.trim(), password);
      if (user) {
        onLogin(user);
      } else {
        setError("Invalid email or password.");
      }
      setLoading(false);
    }, 400);
  }

  function quickLogin(u: typeof DEMO_USERS[number]) {
    setEmail(u.email);
    setPassword(u.password);
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ backgroundColor: "var(--background)" }}
    >
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="mb-3">
            <polygon points="50,5 95,85 5,85" fill="none" stroke="#00A551" strokeWidth="5"/>
            <line x1="50" y1="5" x2="50" y2="85" stroke="#1A6FE0" strokeWidth="2" strokeDasharray="5 3"/>
            <line x1="50" y1="45" x2="90" y2="85" stroke="#00C9A7" strokeWidth="2"/>
            <line x1="50" y1="45" x2="68" y2="85" stroke="#22D678" strokeWidth="2"/>
            <line x1="50" y1="45" x2="55" y2="85" stroke="#00A551" strokeWidth="2"/>
            <line x1="50" y1="45" x2="40" y2="85" stroke="#1A6FE0" strokeWidth="2"/>
            <line x1="50" y1="45" x2="22" y2="85" stroke="#00C9A7" strokeWidth="2"/>
          </svg>
          <h1 className="text-2xl font-bold" style={{ fontFamily: "var(--font-display)", color: "var(--foreground)" }}>
            DataPrism<span style={{ color: "var(--accent-1)" }}>AI</span>
          </h1>
          <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>
            Prisming your data into insights
          </p>
        </div>

        {/* Login card */}
        <div
          className="rounded-2xl p-6 shadow-xl"
          style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}
        >
          <h2 className="text-base font-semibold mb-4" style={{ color: "var(--foreground)" }}>
            Sign in to your workspace
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                placeholder="you@dataprismai.io"
                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                style={{
                  backgroundColor: "var(--panel-bg)",
                  border: "1px solid var(--card-border)",
                  color: "var(--foreground)",
                }}
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1" style={{ color: "var(--muted)" }}>
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                style={{
                  backgroundColor: "var(--panel-bg)",
                  border: "1px solid var(--card-border)",
                  color: "var(--foreground)",
                }}
              />
            </div>

            {error && (
              <div className="rounded-lg px-3 py-2 text-xs" style={{ backgroundColor: "rgba(239,68,68,0.1)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.3)" }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl py-2.5 text-sm font-semibold transition-opacity disabled:opacity-50"
              style={{ backgroundColor: "var(--accent-1)", color: "white" }}
            >
              {loading ? "Signing in…" : "Sign In →"}
            </button>
          </form>
        </div>

        {/* Quick login demo accounts */}
        <div className="mt-5">
          <div className="text-center text-[10px] mb-3 uppercase tracking-widest" style={{ color: "var(--muted)" }}>
            Demo Accounts — click to prefill
          </div>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_USERS.map((u) => {
              const personaColor = PERSONA_COLORS[u.persona] ?? "var(--accent-1)";
              const domainColor  = DOMAIN_COLORS[u.default_domain] ?? "var(--accent-3)";
              return (
                <button
                  key={u.id}
                  onClick={() => quickLogin(u)}
                  className="rounded-xl p-3 text-left transition-opacity hover:opacity-80 flex flex-col gap-1"
                  style={{ backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}
                >
                  {/* Name */}
                  <div className="text-xs font-semibold truncate" style={{ color: "var(--foreground)" }}>{u.name}</div>
                  {/* Persona badge */}
                  <div className="text-[10px] font-medium rounded px-1.5 py-0.5 self-start"
                    style={{ backgroundColor: `${personaColor}20`, color: personaColor, border: `1px solid ${personaColor}40` }}>
                    {ROLE_LABEL[u.role] ?? u.role}
                  </div>
                  {/* Department */}
                  <div className="text-[10px]" style={{ color: "var(--muted)" }}>{u.department}</div>
                  {/* Domain pills */}
                  <div className="flex flex-wrap gap-0.5 mt-0.5">
                    {u.allowed_domains.slice(0, 3).map(d => (
                      <span key={d} className="text-[9px] rounded px-1 py-0.5"
                        style={{ backgroundColor: `${DOMAIN_COLORS[d] ?? "#888"}18`, color: DOMAIN_COLORS[d] ?? "var(--muted)" }}>
                        {d}
                      </span>
                    ))}
                    {u.allowed_domains.length > 3 && (
                      <span className="text-[9px]" style={{ color: "var(--muted)" }}>+{u.allowed_domains.length - 3}</span>
                    )}
                  </div>
                  {/* Default domain */}
                  <div className="text-[9px] mt-0.5" style={{ color: domainColor }}>
                    ◉ {u.default_domain}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-6 text-center text-[10px]" style={{ color: "var(--muted)" }}>
          © {new Date().getFullYear()} DataPrismAI. All rights reserved.
        </div>
      </div>
    </div>
  );
}

