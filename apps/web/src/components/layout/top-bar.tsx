"use client";

import { useEffect, useState } from "react";
import { clearUser } from "@/lib/auth";

type ModelInfo = {
  name: string;
  pulled: boolean;
  loaded: boolean;
  active: boolean;
};

type TopBarProps = {
  theme: "dark" | "dawn";
  onThemeToggle: () => void;
  userName?: string;
  onLogout?: () => void;
  onHelpOpen?: () => void;
  chatMode?: string;
  onChatModeChange?: (m: string) => void;
};

export function TopBar({ theme, onThemeToggle, userName, onLogout, onHelpOpen, chatMode, onChatModeChange }: TopBarProps) {
  const [activeModel, setActiveModel] = useState<string>("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [switching, setSwitching] = useState(false);

  useEffect(() => {
    fetch("/api/model")
      .then((r) => r.json())
      .then((d) => {
        setActiveModel(d.active_model ?? "");
        setModels(d.available_models ?? []);
      })
      .catch(() => {});
  }, []);

  async function handleModelSwitch(name: string) {
    if (name === activeModel || switching) return;
    setSwitching(true);
    try {
      const r = await fetch("/api/model/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: name }),
      });
      const d = await r.json();
      if (r.ok) {
        setActiveModel(d.to);
        setModels((prev) =>
          prev.map((m) => ({ ...m, active: m.name === d.to }))
        );
      } else {
        alert(d.detail ?? "Switch failed");
      }
    } finally {
      setSwitching(false);
    }
  }

  function handleLogout() {
    clearUser();
    onLogout?.();
  }

  // Models that exceed 8 GB VRAM run on CPU (slow) on this hardware
  const CPU_MODELS = new Set(["qwen2.5:32b", "deepseek-r1:32b"]);

  const modelLabel = (name: string) => {
    if (name.startsWith("qwen2.5:")) return { title: "Qwen 2.5", size: name.split(":")[1].toUpperCase() };
    if (name.startsWith("deepseek-r1:")) return { title: "DeepSeek-R1", size: name.split(":")[1].toUpperCase() };
    if (name.startsWith("llama")) return { title: "Llama", size: name.split(":")[1]?.toUpperCase() ?? "" };
    const [base, tag] = name.split(":");
    return { title: base, size: tag?.toUpperCase() ?? "" };
  };

  return (
    <header
      className="flex h-13 shrink-0 items-center justify-between px-4 gap-3"
      style={{
        backgroundColor: "var(--panel-bg)",
        borderBottom: "1px solid var(--card-border)",
        minHeight: "52px",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-2.5 min-w-0 shrink-0">
        <svg width="26" height="26" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="50,5 95,85 5,85" fill="none" stroke="#00A551" strokeWidth="5"/>
          <line x1="50" y1="5" x2="50" y2="85" stroke="#1A6FE0" strokeWidth="2" strokeDasharray="5 3"/>
          <line x1="50" y1="45" x2="90" y2="85" stroke="#00C9A7" strokeWidth="2"/>
          <line x1="50" y1="45" x2="68" y2="85" stroke="#22D678" strokeWidth="2"/>
          <line x1="50" y1="45" x2="55" y2="85" stroke="#00A551" strokeWidth="2"/>
          <line x1="50" y1="45" x2="40" y2="85" stroke="#1A6FE0" strokeWidth="2"/>
          <line x1="50" y1="45" x2="22" y2="85" stroke="#00C9A7" strokeWidth="2"/>
        </svg>
        <div className="leading-tight">
          <div className="text-sm font-bold tracking-tight" style={{ fontFamily: "var(--font-display)" }}>
            <span style={{ color: "var(--foreground)" }}>DataPrism</span>
            <span style={{ color: "var(--accent-1)" }}>AI</span>
          </div>
          <div className="text-[9px] leading-none" style={{ color: "var(--muted)" }}>Prisming your data into insights</div>
        </div>
      </div>

      {/* Center tagline */}
      <div className="flex-1 text-center hidden md:block px-4 min-w-0">
        <div className="text-[11px] font-semibold leading-tight" style={{ color: "var(--accent-1)", fontFamily: "var(--font-sans)" }}>
          Data Intelligence — Ask questions in plain English
        </div>
        <div className="text-[10px] leading-tight" style={{ color: "var(--muted)", fontFamily: "var(--font-sans)" }}>
          DataPrismAI generates and surfaces insights
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2 shrink-0">
        {/* ── Query Mode compact selector ──────────────────────────────── */}
        {onChatModeChange && (
          <div className="flex items-center gap-1" style={{ borderRight: "1px solid var(--card-border)", paddingRight: "8px", marginRight: "2px" }}>
            <span className="text-[9px] font-semibold uppercase tracking-widest mr-1" style={{ color: "var(--muted)" }}>Mode</span>
            {([
              { label: "⚡", value: "pattern", title: "Pattern — Deterministic SQL" },
              { label: "★", value: "hybrid",  title: "Hybrid — Recommended" },
              { label: "🤖", value: "llm",     title: "LLM — Full AI context" },
              { label: "💬", value: "general",  title: "General — Open Q&A, no data context" },
            ] as { label: string; value: string; title: string }[]).map(m => {
              const active = (chatMode || "hybrid") === m.value;
              return (
                <button key={m.value} onClick={() => onChatModeChange(m.value)} title={m.title}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold transition-all"
                  style={{
                    border: active ? "1.5px solid var(--accent-1)" : "1px solid var(--card-border)",
                    backgroundColor: active ? "rgba(0,165,81,0.12)" : "var(--tag-bg)",
                    color: active ? "var(--accent-1)" : "var(--muted)",
                    minWidth: "26px", cursor: "pointer",
                  }}
                >{m.label}</button>
              );
            })}
          </div>
        )}
        {/* ── Model switcher tiles ──────────────────────────────────── */}
        {models.length > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-semibold uppercase tracking-widest mr-0.5" style={{ color: "var(--muted)" }}>Model</span>
            {models.map((m) => {
              const { title, size } = modelLabel(m.name);
              const isCpuModel = CPU_MODELS.has(m.name);
              const isDisabled = !m.pulled || switching;
              return (
                <button
                  key={m.name}
                  onClick={() => !isDisabled && handleModelSwitch(m.name)}
                  disabled={isDisabled}
                  title={
                    !m.pulled
                      ? `${m.name} — not downloaded · Run: ollama pull ${m.name}`
                      : isCpuModel
                      ? `${m.name} — exceeds 8 GB VRAM, runs on CPU (slow). Use 7B models for fast responses.`
                      : m.active
                      ? `Active model: ${m.name}${m.loaded ? " (loaded in memory)" : ""}`
                      : `Switch to ${m.name} (GPU ⚡ fast)`
                  }
                  className="flex flex-col items-start rounded-lg px-2.5 py-1.5 transition-all"
                  style={{
                    minWidth: "72px",
                    border: m.active
                      ? "1.5px solid var(--accent-1)"
                      : "1px solid var(--card-border)",
                    backgroundColor: m.active
                      ? "rgba(0,165,81,0.10)"
                      : !m.pulled
                      ? "var(--tag-bg)"
                      : "var(--tag-bg)",
                    opacity: !m.pulled ? 0.42 : switching && !m.active ? 0.6 : 1,
                    cursor: isDisabled ? "not-allowed" : "pointer",
                    filter: !m.pulled ? "grayscale(0.6)" : "none",
                  }}
                >
                  {/* Title row */}
                  <div className="flex items-center gap-1 w-full">
                    <span
                      className="text-[10px] font-bold leading-none"
                      style={{ color: m.active ? "var(--accent-1)" : !m.pulled ? "var(--muted)" : "var(--foreground)" }}
                    >
                      {title}
                    </span>
                    {m.active && m.loaded && (
                      <span className="ml-auto inline-block w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: "#00A551" }} />
                    )}
                    {!m.pulled && (
                      <span className="ml-auto text-[9px] leading-none" style={{ color: "var(--muted)" }} title="Not downloaded">⬇</span>
                    )}
                    {m.pulled && isCpuModel && (
                      <span className="ml-auto text-[9px] leading-none" style={{ color: "#f59e0b" }} title="Runs on CPU — slow">🐢</span>
                    )}
                  </div>
                  {/* Size + status row */}
                  <div className="flex items-center gap-1 mt-0.5">
                    <span
                      className="text-[9px] font-semibold leading-none rounded px-1 py-0.5"
                      style={{
                        backgroundColor: m.active ? "rgba(0,165,81,0.18)" : "rgba(128,128,128,0.12)",
                        color: m.active ? "var(--accent-1)" : "var(--muted)",
                      }}
                    >
                      {size}
                    </span>
                    <span
                      className="text-[9px] leading-none"
                      style={{ color: m.active ? "var(--accent-2, var(--accent-1))" : "var(--muted)" }}
                    >
                      {switching && m.name === activeModel
                        ? "switching…"
                        : m.active
                        ? "active"
                        : !m.pulled
                        ? "not pulled"
                        : "available"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Workspace name */}
        {userName && (
          <span
            className="hidden sm:block text-xs font-medium truncate max-w-36"
            style={{ color: "var(--muted)" }}
          >
            {userName}&apos;s Workspace
          </span>
        )}

        {/* Theme toggle */}
        <button
          onClick={onThemeToggle}
          className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
          style={{
            border: "1px solid var(--card-border)",
            backgroundColor: "var(--tag-bg)",
            color: "var(--foreground)",
          }}
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? "☀ Light" : "☾ Dark"}
        </button>

        {/* Help */}
        {onHelpOpen && (
          <button
            onClick={onHelpOpen}
            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors hover:opacity-80"
            style={{
              border: "1px solid var(--card-border)",
              backgroundColor: "var(--tag-bg)",
              color: "var(--foreground)",
            }}
            title="Help & Documentation"
          >
            ? Help
          </button>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors hover:opacity-80"
          style={{
            border: "1px solid var(--card-border)",
            backgroundColor: "var(--tag-bg)",
            color: "var(--muted)",
          }}
          title="Sign out"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
