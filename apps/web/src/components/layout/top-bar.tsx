"use client";

import { clearUser } from "@/lib/auth";

type TopBarProps = {
  theme: "dark" | "dawn";
  onThemeToggle: () => void;
  userName?: string;
  onLogout?: () => void;
  onHelpOpen?: () => void;
};

export function TopBar({ theme, onThemeToggle, userName, onLogout, onHelpOpen }: TopBarProps) {
  function handleLogout() {
    clearUser();
    onLogout?.();
  }

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
        <span
          className="text-[11px] leading-tight"
          style={{ color: "var(--muted)", fontFamily: "var(--font-sans)" }}
        >
          <span className="font-semibold" style={{ color: "var(--accent-1)" }}>Data Intelligence</span>
          {" "}— Ask questions in plain English —{" "}
          <span style={{ color: "var(--foreground)" }}>DataPrismAI</span> generates and surfaces insights
        </span>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-2 shrink-0">
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
