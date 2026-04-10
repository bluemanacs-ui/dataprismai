"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchConfig,
  patchConfig,
  resetConfigKey,
  ConfigSection,
  ConfigEntry,
} from "@/lib/api";

// ── Helpers ──────────────────────────────────────────────────────────────────

function sectionIcon(section: ConfigSection) {
  return section.icon ?? "⚙";
}

function entryBadge(entry: ConfigEntry) {
  if (entry.is_readonly)  return { text: "read-only", color: "#6b7280" };
  if (entry.restart_req)  return { text: "restart req.", color: "#f59e0b" };
  if (entry.overridden)   return { text: "overridden", color: "#3b82f6" };
  return null;
}

// ── Modes at a Glance card ────────────────────────────────────────────────────

const TABLE_STRATEGY_LABELS: Record<string, string> = {
  semantic_first: "Semantic First",
  raw_first:      "Raw First",
  auto:           "Auto",
};

const INTENT_LABELS: Record<string, string> = {
  metric_query:  "Metric",
  insight_query: "Insight",
  preview_data:  "Preview",
};

type ModeItem =
  | { kind: "value"; label: string; value: string; map?: Record<string, string> }
  | { kind: "bool"; label: string; value: string };

function ModesCard({ configMap }: { configMap: Record<string, string> }) {
  const cv = (key: string, fallback = "—") => configMap[key] ?? fallback;

  const valueItems: ModeItem[] = [
    { kind: "value", label: "Primary LLM",     value: cv("llm.model") },
    { kind: "value", label: "General LLM",     value: cv("llm.general_model") },
    { kind: "value", label: "Table Strategy",  value: cv("semantic.preferred_table_strategy"), map: TABLE_STRATEGY_LABELS },
    { kind: "value", label: "Query Engine",    value: cv("router.primary_engine") },
    { kind: "value", label: "Catalog Source",  value: cv("semantic.catalog_source") },
    { kind: "value", label: "Default Intent",  value: cv("planner.default_intent"), map: INTENT_LABELS },
  ];

  const toggleItems: ModeItem[] = [
    { kind: "bool", label: "Guardrail",        value: cv("guardrail.enabled",                  "true") },
    { kind: "bool", label: "Vanna SQL",        value: cv("vanna.enabled",                      "false") },
    { kind: "bool", label: "Entity Resolver",  value: cv("graph.enable_entity_resolver",       "true") },
    { kind: "bool", label: "SQL Validator",    value: cv("graph.enable_sql_validator",         "true") },
    { kind: "bool", label: "Chart Rec.",       value: cv("graph.enable_chart_recommendation",  "true") },
    { kind: "bool", label: "Thread Memory",    value: cv("graph.enable_thread_memory",         "false") },
    { kind: "bool", label: "LLM Planner",      value: cv("planner.enable_llm_fallback",        "true") },
  ];

  return (
    <div
      className="rounded-2xl p-4 space-y-3"
      style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-base">🗺</span>
        <span className="text-xs font-bold" style={{ color: "var(--foreground)", fontFamily: "var(--font-display)" }}>
          Operational Modes at a Glance
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: "rgba(0,165,81,0.1)", color: "var(--accent-1)", border: "1px solid rgba(0,165,81,0.25)" }}>
          live config
        </span>
      </div>

      {/* Model / strategy chips */}
      <div className="flex flex-wrap gap-2">
        {valueItems.map((item) => {
          const display = (item.kind === "value" && item.map) ? (item.map[item.value] ?? item.value) : item.value;
          return (
            <div
              key={item.label}
              className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[11px]"
              style={{ backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}
            >
              <span style={{ color: "var(--muted)" }}>{item.label}</span>
              <span className="font-semibold" style={{ color: "var(--foreground)" }}>{display}</span>
            </div>
          );
        })}
      </div>

      {/* Feature toggles */}
      <div className="flex flex-wrap gap-2">
        {toggleItems.map((item) => {
          const on = item.value === "true";
          return (
            <div
              key={item.label}
              className="flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[11px]"
              style={{
                backgroundColor: on ? "rgba(0,165,81,0.08)" : "var(--panel-bg)",
                border: `1px solid ${on ? "rgba(0,165,81,0.35)" : "var(--card-border)"}`,
              }}
            >
              <span
                className="h-2 w-2 rounded-full inline-block"
                style={{ backgroundColor: on ? "var(--accent-1)" : "#6b7280" }}
              />
              <span style={{ color: on ? "var(--accent-1)" : "var(--muted)" }}>{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Input renderer ────────────────────────────────────────────────────────────

function ConfigInput({
  entry,
  value,
  onChange,
}: {
  entry: ConfigEntry;
  value: string;
  onChange: (v: string) => void;
}) {
  const [showPwd, setShowPwd] = useState(false);
  const baseStyle: React.CSSProperties = {
    backgroundColor: "var(--panel-bg)",
    border: "1px solid var(--card-border)",
    color: entry.is_readonly ? "var(--muted)" : "var(--foreground)",
    borderRadius: 8,
    padding: "6px 10px",
    fontSize: 12,
    width: "100%",
    opacity: entry.is_readonly ? 0.65 : 1,
    cursor: entry.is_readonly ? "not-allowed" : "auto",
    fontFamily: "var(--font-mono)",
  };

  if (entry.input_type === "boolean") {
    return (
      <button
        disabled={entry.is_readonly}
        onClick={() => onChange(value === "true" ? "false" : "true")}
        className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
        style={{
          backgroundColor: value === "true" ? "rgba(0,165,81,0.15)" : "var(--panel-bg)",
          border: `1px solid ${value === "true" ? "var(--accent-1)" : "var(--card-border)"}`,
          color: value === "true" ? "var(--accent-1)" : "var(--muted)",
          opacity: entry.is_readonly ? 0.55 : 1,
          cursor: entry.is_readonly ? "not-allowed" : "pointer",
        }}
      >
        <span
          className="inline-block h-3 w-3 rounded-full"
          style={{ backgroundColor: value === "true" ? "var(--accent-1)" : "var(--muted)" }}
        />
        {value === "true" ? "Enabled" : "Disabled"}
      </button>
    );
  }

  if (entry.input_type === "select") {
    return (
      <select
        disabled={entry.is_readonly}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ ...baseStyle, paddingRight: 28 }}
      >
        {entry.options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    );
  }

  if (entry.input_type === "textarea") {
    return (
      <textarea
        disabled={entry.is_readonly}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={3}
        style={{ ...baseStyle, resize: "vertical" }}
      />
    );
  }

  if (entry.input_type === "password") {
    return (
      <div className="relative flex items-center">
        <input
          type={showPwd ? "text" : "password"}
          disabled={entry.is_readonly}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{ ...baseStyle, paddingRight: 36 }}
        />
        {!entry.is_readonly && (
          <button
            type="button"
            onClick={() => setShowPwd((p) => !p)}
            className="absolute right-2 text-xs"
            style={{ color: "var(--muted)" }}
          >
            {showPwd ? "hide" : "show"}
          </button>
        )}
      </div>
    );
  }

  return (
    <input
      type={entry.input_type === "number" ? "number" : "text"}
      disabled={entry.is_readonly}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={baseStyle}
    />
  );
}

// ── Section card ──────────────────────────────────────────────────────────────

function SectionCard({
  section,
  draftValues,
  dirtyKeys,
  saving,
  onValueChange,
  onSaveSection,
  onResetKey,
}: {
  section: ConfigSection;
  draftValues: Record<string, string>;
  dirtyKeys: Set<string>;
  saving: boolean;
  onValueChange: (key: string, value: string) => void;
  onSaveSection: (sectionId: string) => void;
  onResetKey: (key: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const sectionDirty = section.entries.some((e) => dirtyKeys.has(e.key));

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}
    >
      {/* Header */}
      <button
        className="w-full flex items-center justify-between px-5 py-4"
        onClick={() => setExpanded((v) => !v)}
        style={{ backgroundColor: "var(--panel-bg)", borderBottom: expanded ? "1px solid var(--card-border)" : "none" }}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{sectionIcon(section)}</span>
          <div className="text-left">
            <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>
              {section.label}
            </div>
            <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
              {section.description}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {sectionDirty && (
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{ backgroundColor: "rgba(59,130,246,0.1)", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.3)" }}
            >
              unsaved
            </span>
          )}
          <span style={{ color: "var(--muted)", fontSize: 12 }}>{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {/* Entries */}
      {expanded && (
        <div className="divide-y" style={{ borderColor: "var(--card-border)" }}>
          {section.entries.map((entry) => {
            const badge = entryBadge(entry);
            const isDirty = dirtyKeys.has(entry.key);
            const currentVal = draftValues[entry.key] ?? entry.value;

            return (
              <div key={entry.key} className="px-5 py-4">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-semibold" style={{ color: "var(--foreground)" }}>
                        {entry.label}
                      </span>
                      {badge && (
                        <span
                          className="rounded px-1.5 py-0.5 text-[10px] font-medium"
                          style={{
                            backgroundColor: `${badge.color}18`,
                            color: badge.color,
                            border: `1px solid ${badge.color}40`,
                          }}
                        >
                          {badge.text}
                        </span>
                      )}
                      {isDirty && !entry.is_readonly && (
                        <span className="rounded px-1.5 py-0.5 text-[10px]"
                          style={{ backgroundColor: "rgba(59,130,246,0.1)", color: "#3b82f6" }}>
                          modified
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] mt-0.5" style={{ color: "var(--muted)" }}>
                      {entry.description}
                    </div>
                    <div className="text-[10px] mt-0.5 font-mono" style={{ color: "var(--muted)", opacity: 0.6 }}>
                      key: {entry.key}
                      {entry.default && entry.default !== entry.value ? (
                        <span className="ml-2" style={{ color: "var(--accent-3)" }}>
                          (default: {entry.is_sensitive ? "•••" : entry.default})
                        </span>
                      ) : null}
                    </div>
                  </div>
                  {!entry.is_readonly && entry.overridden && (
                    <button
                      onClick={() => onResetKey(entry.key)}
                      className="flex-shrink-0 text-[10px] px-2 py-1 rounded"
                      style={{ border: "1px solid var(--card-border)", color: "var(--muted)" }}
                      title="Revert to default/env value"
                    >
                      ↺ reset
                    </button>
                  )}
                </div>
                <ConfigInput
                  entry={entry}
                  value={currentVal}
                  onChange={(v) => onValueChange(entry.key, v)}
                />
              </div>
            );
          })}

          {/* Section Save button */}
          {section.entries.some((e) => !e.is_readonly) && (
            <div className="px-5 py-3 flex items-center justify-between" style={{ backgroundColor: "var(--panel-bg)" }}>
              <div className="text-[11px]" style={{ color: "var(--muted)" }}>
                {sectionDirty
                  ? "You have unsaved changes in this section."
                  : "All changes saved."}
              </div>
              <button
                disabled={!sectionDirty || saving}
                onClick={() => onSaveSection(section.id)}
                className="rounded-lg px-4 py-1.5 text-xs font-semibold transition-all"
                style={
                  sectionDirty
                    ? { backgroundColor: "var(--accent-1)", color: "white" }
                    : { backgroundColor: "var(--panel-bg)", color: "var(--muted)", border: "1px solid var(--card-border)" }
                }
              >
                {saving ? "Saving…" : "Save Section"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main config panel ──────────────────────────────────────────────────────────

export function ConfigPanel() {
  const [sections, setSections] = useState<ConfigSection[]>([]);
  const [totalKeys, setTotalKeys] = useState(0);
  const [overriddenKeys, setOverriddenKeys] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [dirtyKeys, setDirtyKeys] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: "ok" | "err" } | null>(null);
  const [filter, setFilter] = useState("");
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Flat key → current-value map (used by ModesCard)
  const configMap = useMemo(() => {
    const m: Record<string, string> = {};
    sections.forEach((s) => s.entries.forEach((e) => { m[e.key] = e.value; }));
    return m;
  }, [sections]);

  const showToast = useCallback((msg: string, type: "ok" | "err" = "ok") => {
    setToast({ msg, type });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  }, []);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchConfig();
      setSections(data.sections);
      setTotalKeys(data.total_keys);
      setOverriddenKeys(data.overridden_keys);
      // Seed draft with current values
      const initial: Record<string, string> = {};
      data.sections.forEach((s) =>
        s.entries.forEach((e) => { initial[e.key] = e.value; })
      );
      setDraftValues(initial);
      setDirtyKeys(new Set());
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadConfig(); }, [loadConfig]);

  const handleValueChange = useCallback((key: string, value: string) => {
    setDraftValues((prev) => ({ ...prev, [key]: value }));
    setDirtyKeys((prev) => {
      const next = new Set(prev);
      next.add(key);
      return next;
    });
  }, []);

  const handleSaveSection = useCallback(async (sectionId: string) => {
    const section = sections.find((s) => s.id === sectionId);
    if (!section) return;

    const updates: Record<string, string> = {};
    section.entries.forEach((e) => {
      if (!e.is_readonly && dirtyKeys.has(e.key)) {
        updates[e.key] = draftValues[e.key] ?? e.value;
      }
    });
    if (!Object.keys(updates).length) return;

    setSaving(true);
    try {
      await patchConfig(updates);
      setDirtyKeys((prev) => {
        const next = new Set(prev);
        Object.keys(updates).forEach((k) => next.delete(k));
        return next;
      });
      showToast(`Saved ${Object.keys(updates).length} key(s) for "${section.label}".`);
      await loadConfig();
    } catch (err) {
      showToast(String(err), "err");
    } finally {
      setSaving(false);
    }
  }, [sections, dirtyKeys, draftValues, loadConfig, showToast]);

  const handleResetKey = useCallback(async (key: string) => {
    try {
      const res = await resetConfigKey(key);
      showToast(`Reset "${key}" → "${res.reverted_to}".`);
      await loadConfig();
    } catch (err) {
      showToast(String(err), "err");
    }
  }, [loadConfig, showToast]);

  // Filter sections/entries by search
  const filteredSections = filter.trim()
    ? sections
        .map((s) => ({
          ...s,
          entries: s.entries.filter(
            (e) =>
              e.key.includes(filter.toLowerCase()) ||
              e.label.toLowerCase().includes(filter.toLowerCase()) ||
              e.description.toLowerCase().includes(filter.toLowerCase())
          ),
        }))
        .filter((s) => s.entries.length > 0)
    : sections;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-bold" style={{ color: "var(--foreground)", fontFamily: "var(--font-display)" }}>
            Platform Configuration
          </h3>
          <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
            {totalKeys} parameters across {sections.length} sections · {overriddenKeys} DB override{overriddenKeys !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={loadConfig}
          className="rounded-lg px-3 py-1.5 text-xs"
          style={{ border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--panel-bg)" }}
        >
          ↺ Reload
        </button>
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="Search config keys…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full rounded-xl px-4 py-2 text-xs"
        style={{
          backgroundColor: "var(--panel-bg)",
          border: "1px solid var(--card-border)",
          color: "var(--foreground)",
        }}
      />

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-[10px]" style={{ color: "var(--muted)" }}>
        {[
          { color: "#6b7280",  text: "read-only — shown for transparency" },
          { color: "#f59e0b",  text: "restart required" },
          { color: "#3b82f6",  text: "DB override active" },
          { color: "var(--accent-1)", text: "editable" },
        ].map(({ color, text }) => (
          <span key={text} className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
            {text}
          </span>
        ))}
      </div>

      {/* Modes at a Glance — shown once config is loaded */}
      {!loading && sections.length > 0 && <ModesCard configMap={configMap} />}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="thinking-dot inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: "var(--accent-1)", animationDelay: `${i * 0.18}s` }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div
          className="rounded-xl px-4 py-3 text-xs"
          style={{ backgroundColor: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#ef4444" }}
        >
          Failed to load config: {error}
        </div>
      )}

      {/* Section cards */}
      {!loading && !error && (
        <div className="space-y-3">
          {filteredSections.map((section) => (
            <SectionCard
              key={section.id}
              section={section}
              draftValues={draftValues}
              dirtyKeys={dirtyKeys}
              saving={saving}
              onValueChange={handleValueChange}
              onSaveSection={handleSaveSection}
              onResetKey={handleResetKey}
            />
          ))}
          {filteredSections.length === 0 && (
            <div className="py-12 text-center text-xs" style={{ color: "var(--muted)" }}>
              No config entries match &ldquo;{filter}&rdquo;
            </div>
          )}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 right-6 rounded-xl px-4 py-3 text-xs font-medium shadow-xl z-50"
          style={{
            backgroundColor: toast.type === "ok" ? "rgba(0,165,81,0.95)" : "rgba(239,68,68,0.95)",
            color: "white",
            border: "1px solid rgba(255,255,255,0.15)",
            maxWidth: 360,
          }}
        >
          {toast.msg}
        </div>
      )}
    </div>
  );
}
