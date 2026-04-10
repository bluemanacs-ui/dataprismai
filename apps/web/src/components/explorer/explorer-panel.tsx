// =============================================================================
// ExplorerPanel — Data Explorer: Datasets, Profiling, Data Models (ERD),
//                 Semantic Layer, and Query History tabs.
//
// Dependencies: zero external chart/graph libraries — ERD is rendered with
// native SVG. Semantic catalog + table metadata are fetched from the API.
// =============================================================================
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { SemanticCatalogResponse } from "@/types/chat";
import { TableInfo, fetchTableSample, fetchTableProfile, fetchDictionaryTables, fetchDictionaryTableDetail, DicTable, DicColumn, DicRelationship, TableProfile } from "@/lib/api";

type ExplorerTab = "datasets" | "profiling" | "models" | "semantic" | "history" | "dictionary";

type ExplorerPanelProps = {
    catalog?: SemanticCatalogResponse | null;
    tables?: TableInfo[];
    database?: string;
    queryHistory?: { query: string; metric: string; rowCount: number; ts: number }[];
    onQuerySend?: (query: string) => void;
    onRefreshTables?: () => void;
    tablesLoading?: boolean;
};

function ScbBadge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "green" | "blue" | "amber" | "red" }) {
    const styles: Record<string, React.CSSProperties> = {
        default: { backgroundColor: "var(--tag-bg)", color: "var(--muted)" },
        green:   { backgroundColor: "rgba(0,165,81,0.12)", color: "var(--accent-1)" },
        blue:    { backgroundColor: "rgba(26,111,224,0.15)", color: "var(--accent-2)" },
        amber:   { backgroundColor: "rgba(245,158,11,0.12)", color: "#f59e0b" },
        red:     { backgroundColor: "rgba(239,68,68,0.12)", color: "#ef4444" },
    };
    return (
        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium"
            style={styles[variant]}>{children}</span>
    );
}

function ScbTabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
        <button onClick={onClick}
            className="whitespace-nowrap rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
            style={active
                ? { backgroundColor: "var(--accent-1)", color: "white" }
                : { color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
            {children}
        </button>
    );
}

function ScbInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
    return (
        <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
            className="w-full rounded-lg px-3 py-2 text-sm outline-none"
            style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--panel-bg)", color: "var(--foreground)" }} />
    );
}



// ─── Shared table card (used by DatasetsTab) ────────────────────────────────
function TableCard({ t, expanded, onToggle }: { t: TableInfo; expanded: boolean; onToggle: () => void }) {
    const group = tableGroup(t.name);
    const meta  = LAYER_META[group];
    return (
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
            <button onClick={onToggle} className="flex w-full items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                    <span>{meta?.icon ?? "🗃"}</span>
                    <div>
                        <div className="text-sm font-medium text-left" style={{ color: "var(--foreground)" }}>{t.name}</div>
                        <div className="text-xs text-left" style={{ color: "var(--muted)" }}>{t.columns.length} columns</div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <ScbBadge variant="green">{t.row_count.toLocaleString()} rows</ScbBadge>
                    <span style={{ color: "var(--muted)" }} className="text-xs">{expanded ? "▲" : "▼"}</span>
                </div>
            </button>
            {expanded && (
                <div className="px-4 py-3" style={{ borderTop: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead>
                                <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--muted)" }}>
                                    <th className="pb-1.5 text-left font-medium pr-4">Column</th>
                                    <th className="pb-1.5 text-left font-medium pr-4">Type</th>
                                    <th className="pb-1.5 text-left font-medium pr-4">Nullable</th>
                                    <th className="pb-1.5 text-left font-medium">Key</th>
                                </tr>
                            </thead>
                            <tbody>
                                {t.columns.map((c, i) => (
                                    <tr key={i} style={{ borderBottom: "1px solid var(--card-border)" }}>
                                        <td className="py-1.5 pr-4 font-mono" style={{ color: "var(--foreground)" }}>{c.name}</td>
                                        <td className="py-1.5 pr-4 font-mono" style={{ color: "var(--accent-3)" }}>{c.type}</td>
                                        <td className="py-1.5 pr-4" style={{ color: "var(--muted)" }}>{c.nullable === "YES" ? "✓" : "✗"}</td>
                                        <td className="py-1.5">
                                            {c.key === "PRI" ? <ScbBadge variant="amber">PK</ScbBadge>
                                                : c.key === "MUL" ? <ScbBadge variant="blue">IDX</ScbBadge>
                                                : <span style={{ color: "var(--card-border)" }}>—</span>}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

function DatasetsTab({ tables, database }: { tables: TableInfo[]; database: string }) {
    const [expanded, setExpanded] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    // All groups collapsed by default; expand with search or click
    const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set(LAYER_ORDER));

    const grouped = useMemo(() => {
        const q = search.toLowerCase();
        const filtered = tables.filter(t => !q || t.name.toLowerCase().includes(q));
        const map: Record<string, TableInfo[]> = {};
        for (const t of filtered) {
            const g = tableGroup(t.name);
            (map[g] = map[g] ?? []).push(t);
        }
        return map;
    }, [tables, search]);

    // Auto-expand matching groups when searching
    useEffect(() => {
        if (search.trim()) {
            setCollapsedGroups(new Set(LAYER_ORDER.filter(g => !grouped[g]?.length)));
        }
    }, [search, grouped]);

    function toggleGroup(g: string) {
        setCollapsedGroups(prev => {
            const next = new Set(prev);
            next.has(g) ? next.delete(g) : next.add(g);
            return next;
        });
    }

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Tables</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    DB: <span style={{ color: "var(--accent-2)" }}>{database}</span> · {tables.length} tables
                </div>
            </div>
            <ScbInput value={search} onChange={setSearch} placeholder="Search tables..." />
            <div className="space-y-4">
                {LAYER_ORDER.filter(g => grouped[g]?.length).map(g => {
                    const meta    = LAYER_META[g];
                    const layerTs = grouped[g];
                    const collapsed = collapsedGroups.has(g);
                    return (
                        <div key={g}>
                            <button onClick={() => toggleGroup(g)}
                                className="flex w-full items-center gap-2 mb-2 py-1.5 px-2 rounded-lg"
                                style={{ background: `${meta?.color ?? "#64748b"}15` }}>
                                <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                                    style={{ background: `${meta?.color ?? "#64748b"}22`, color: meta?.color ?? "#64748b" }}>
                                    {meta?.icon} {meta?.label ?? g}
                                </span>
                                <span className="text-[10px]" style={{ color: "var(--muted)" }}>{layerTs.length} tables</span>
                                <span className="ml-auto text-[10px]" style={{ color: "var(--muted)" }}>{collapsed ? "▶" : "▼"}</span>
                            </button>
                            {!collapsed && (
                                <div className="space-y-2">
                                    {layerTs.map(t => (
                                        <TableCard key={t.name} t={t}
                                            expanded={expanded === t.name}
                                            onToggle={() => setExpanded(expanded === t.name ? null : t.name)} />
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
                {!Object.keys(grouped).length && (
                    <div className="py-8 text-center text-sm" style={{ color: "var(--muted)" }}>
                        {tables.length === 0 ? "Loading tables…" : "No tables found"}
                    </div>
                )}
            </div>
        </div>
    );
}
const SAMPLE_PAGE = 10;

function ProfilingTab({ tables, onQuerySend }: { tables: TableInfo[]; onQuerySend?: (q: string) => void }) {
    const [selectedTable, setSelectedTable] = useState<string>(tables[0]?.name ?? "");
    const [sampleOpen, setSampleOpen] = useState(false);
    const [sampleRows, setSampleRows] = useState<Record<string, string | null>[]>([]);
    const [sampleLoading, setSampleLoading] = useState(false);
    const [sampleMoreLoading, setSampleMoreLoading] = useState(false);
    const [sampleHasMore, setSampleHasMore] = useState(false);
    const [profile, setProfile] = useState<TableProfile | null>(null);
    const [profileLoading, setProfileLoading] = useState(false);
    const table = tables.find(t => t.name === selectedTable);

    useEffect(() => {
        setSampleOpen(false);
        setSampleRows([]);
        setSampleHasMore(false);
        setProfile(null);
        if (!selectedTable) return;
        setProfileLoading(true);
        fetchTableProfile(selectedTable).then(p => { setProfile(p); setProfileLoading(false); }).catch(() => setProfileLoading(false));
    }, [selectedTable]);

    async function handleSampleToggle() {
        if (sampleOpen) { setSampleOpen(false); return; }
        setSampleOpen(true);
        if (sampleRows.length === 0 && table && table.row_count > 0) {
            setSampleLoading(true);
            const result = await fetchTableSample(selectedTable, SAMPLE_PAGE, 0);
            setSampleRows(result.rows);
            setSampleHasMore(result.rows.length === SAMPLE_PAGE && table.row_count > SAMPLE_PAGE);
            setSampleLoading(false);
        }
    }

    async function handleLoadMore() {
        if (!table) return;
        setSampleMoreLoading(true);
        const result = await fetchTableSample(selectedTable, SAMPLE_PAGE, sampleRows.length);
        const combined = [...sampleRows, ...result.rows];
        setSampleRows(combined);
        setSampleHasMore(result.rows.length === SAMPLE_PAGE && combined.length < table.row_count);
        setSampleMoreLoading(false);
    }

    if (!tables.length) return <div className="py-10 text-center text-sm" style={{ color: "var(--muted)" }}>No tables loaded</div>;

    // Merge column schema info with profile stats
    const profileCols = profile?.columns ?? [];
    const schemaCols = table?.columns ?? [];
    const mergedCols = schemaCols.map(sc => {
        const pc = profileCols.find(c => c.name === sc.name);
        return { ...sc, ...pc };
    });

    const nullableCols = schemaCols.filter(c => c.nullable === "YES").length;
    const pkCols = schemaCols.filter(c => c.key === "PRI" || c.key === "UNI").length;

    return (
        <div className="space-y-4">
            <div>
                <div className="text-sm font-semibold mb-2" style={{ color: "var(--foreground)" }}>Data Profiling</div>
                <select value={selectedTable} onChange={e => setSelectedTable(e.target.value)}
                    className="w-full rounded-lg px-3 py-2 text-sm cursor-pointer"
                    style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--tag-bg)", color: "var(--foreground)" }}>
                    {(() => {
                        const grouped: Record<string, TableInfo[]> = {};
                        for (const t of tables) {
                            const g = tableGroup(t.name);
                            (grouped[g] = grouped[g] ?? []).push(t);
                        }
                        return LAYER_ORDER.filter(g => grouped[g]?.length).map(g => (
                            <optgroup key={g} label={`${LAYER_META[g]?.icon ?? ""} ${LAYER_META[g]?.label ?? g}`}>
                                {grouped[g].map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                            </optgroup>
                        ));
                    })()}
                </select>
            </div>
            {table && (
                <>
                    <div className="grid grid-cols-4 gap-2 mt-3">
                        {([
                            { label: "Total Rows", value: (profile?.total_rows ?? table.row_count).toLocaleString(), color: "var(--accent-1)" },
                            { label: "Columns", value: schemaCols.length.toString(), color: "var(--accent-2)" },
                            { label: "Nullable", value: nullableCols.toString(), color: "#f59e0b" },
                            { label: "Keys / Unique", value: pkCols.toString(), color: "#00A551" },
                        ] as { label: string; value: string; color: string }[]).map(k => (
                            <div key={k.label} className="rounded-xl p-3 text-center" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                <div className="text-[10px] uppercase tracking-wide mb-1" style={{ color: "var(--muted)" }}>{k.label}</div>
                                <div className="text-lg font-bold" style={{ color: k.color }}>{k.value}</div>
                            </div>
                        ))}
                    </div>
                    <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                        <div className="flex items-center justify-between px-4 py-2.5" style={{ backgroundColor: "var(--tag-bg)" }}>
                            <span className="text-xs font-semibold" style={{ color: "var(--accent-3)" }}>Column Profile</span>
                            {profileLoading && <span className="text-[10px]" style={{ color: "var(--muted)" }}>Loading stats…</span>}
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--muted)" }}>
                                        <th className="px-3 py-2 text-left font-medium">Column</th>
                                        <th className="px-3 py-2 text-left font-medium">Type</th>
                                        <th className="px-3 py-2 text-center font-medium">Key</th>
                                        <th className="px-3 py-2 text-right font-medium">Nullable</th>
                                        <th className="px-3 py-2 text-right font-medium">Null %</th>
                                        <th className="px-3 py-2 text-right font-medium">Distinct</th>
                                        <th className="px-3 py-2 text-right font-medium">Min</th>
                                        <th className="px-3 py-2 text-right font-medium">Max</th>
                                        <th className="px-3 py-2 text-right font-medium">Avg</th>
                                        <th className="px-3 py-2 text-left font-medium">Distribution</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {mergedCols.map((c, i) => {
                                        const pc = profileCols.find(p => p.name === c.name);
                                        const nullPct = pc?.null_pct ?? null;
                                        const isHigh = nullPct !== null && nullPct > 50;
                                        const topVals = pc?.top_values;
                                        const maxCount = topVals && topVals.length > 0 ? topVals[0].count : 0;
                                        return (
                                            <tr key={i} style={{ borderBottom: "1px solid var(--card-border)", backgroundColor: i % 2 ? "var(--step-bg)" : "transparent" }}>
                                                <td className="px-3 py-1.5 font-mono" style={{ color: "var(--foreground)" }}>{c.name}</td>
                                                <td className="px-3 py-1.5 font-mono" style={{ color: "var(--accent-3)" }}>{c.type}</td>
                                                <td className="px-3 py-1.5 text-center">
                                                    {c.key === "PRI" ? <span className="rounded px-1.5 py-0.5 text-[9px] font-bold" style={{ backgroundColor: "#00A55122", color: "#00A551" }}>PK</span>
                                                    : c.key === "UNI" ? <span className="rounded px-1.5 py-0.5 text-[9px] font-bold" style={{ backgroundColor: "#1A6FE022", color: "#1A6FE0" }}>UK</span>
                                                    : c.key === "MUL" ? <span className="rounded px-1.5 py-0.5 text-[9px] font-bold" style={{ backgroundColor: "#f59e0b22", color: "#f59e0b" }}>IDX</span>
                                                    : <span style={{ color: "var(--muted)" }}>—</span>}
                                                </td>
                                                <td className="px-3 py-1.5 text-right" style={{ color: c.nullable === "YES" ? "#f59e0b" : "var(--muted)" }}>
                                                    {c.nullable === "YES" ? "Yes" : "No"}
                                                </td>
                                                <td className="px-3 py-1.5 text-right font-mono" style={{ color: isHigh ? "#ef4444" : "var(--muted)" }}>
                                                    {nullPct !== null ? `${nullPct.toFixed(1)}%` : <span style={{ color: "var(--muted)" }}>—</span>}
                                                </td>
                                                <td className="px-3 py-1.5 text-right font-mono" style={{ color: "var(--foreground)" }}>
                                                    {pc?.distinct_count !== undefined && pc.distinct_count !== null
                                                        ? pc.distinct_count.toLocaleString()
                                                        : <span style={{ color: "var(--muted)" }}>—</span>}
                                                </td>
                                                <td className="px-3 py-1.5 text-right font-mono max-w-20 truncate" style={{ color: "var(--muted)" }}
                                                    title={pc?.min_val ?? undefined}>
                                                    {pc?.min_val ?? "—"}
                                                </td>
                                                <td className="px-3 py-1.5 text-right font-mono max-w-20 truncate" style={{ color: "var(--muted)" }}
                                                    title={pc?.max_val ?? undefined}>
                                                    {pc?.max_val ?? "—"}
                                                </td>
                                                <td className="px-3 py-1.5 text-right font-mono" style={{ color: "var(--muted)" }}>
                                                    {pc?.avg_val !== null && pc?.avg_val !== undefined ? Number(pc.avg_val).toFixed(2) : "—"}
                                                </td>
                                                <td className="px-3 py-1.5 min-w-28">
                                                    {topVals && topVals.length > 0 ? (
                                                        <div className="space-y-0.5">
                                                            {topVals.slice(0, 3).map((tv, ti) => (
                                                                <div key={ti} className="flex items-center gap-1">
                                                                    <div className="h-1.5 rounded-full" style={{
                                                                        width: `${Math.round((tv.count / maxCount) * 56)}px`,
                                                                        minWidth: 2,
                                                                        backgroundColor: "var(--accent-2)",
                                                                        opacity: 0.6 + ti * -0.15
                                                                    }} />
                                                                    <span className="text-[9px] truncate max-w-16" style={{ color: "var(--muted)" }}
                                                                        title={String(tv.value)}>{String(tv.value)}</span>
                                                                    <span className="text-[9px] ml-auto" style={{ color: "var(--accent-2)" }}>{tv.pct?.toFixed(0)}%</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    ) : <span style={{ color: "var(--muted)", fontSize: "9px" }}>—</span>}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    {table.row_count === 0 ? (
                        <div className="rounded-xl px-4 py-6 text-center text-sm" style={{ border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--step-bg)" }}>
                            No data — table is empty
                        </div>
                    ) : (
                        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                            <button onClick={handleSampleToggle}
                                className="flex w-full items-center justify-between px-4 py-2.5 text-xs font-semibold"
                                style={{ backgroundColor: "var(--tag-bg)", color: "var(--foreground)" }}>
                                <span>📋 Sample Data</span>
                                <span style={{ color: "var(--muted)" }}>
                                    {sampleOpen && sampleRows.length > 0 ? `${sampleRows.length} / ${table.row_count.toLocaleString()} rows` : ""}
                                    {" "}{sampleOpen ? "▲" : "▼"}
                                </span>
                            </button>
                            {sampleOpen && (
                                <div style={{ borderTop: "1px solid var(--card-border)" }}>
                                    {sampleLoading ? (
                                        <div className="px-4 py-4 text-xs text-center" style={{ color: "var(--muted)" }}>Loading…</div>
                                    ) : sampleRows.length === 0 ? (
                                        <div className="px-4 py-4 text-xs text-center" style={{ color: "var(--muted)" }}>No rows returned</div>
                                    ) : (
                                        <>
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-xs">
                                                    <thead>
                                                        <tr style={{ borderBottom: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                                            {Object.keys(sampleRows[0]).map(col => (
                                                                <th key={col} className="px-3 py-2 text-left font-medium whitespace-nowrap"
                                                                    style={{ color: "var(--muted)" }}>{col}</th>
                                                            ))}
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {sampleRows.map((row, i) => (
                                                            <tr key={i} style={{ borderBottom: "1px solid var(--card-border)", backgroundColor: i % 2 ? "var(--step-bg)" : "transparent" }}>
                                                                {Object.values(row).map((val, j) => (
                                                                    <td key={j} className="px-3 py-1.5 font-mono whitespace-nowrap max-w-40 overflow-hidden text-ellipsis"
                                                                        style={{ color: "var(--foreground)" }} title={val ?? "NULL"}>
                                                                        {val === null ? <span style={{ color: "var(--muted)" }}>NULL</span> : val}
                                                                    </td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                            <div className="flex items-center justify-between px-4 py-2.5"
                                                style={{ borderTop: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                                <span className="text-[10px]" style={{ color: "var(--muted)" }}>
                                                    Showing {sampleRows.length} of {table.row_count.toLocaleString()} rows · {SAMPLE_PAGE} per block
                                                </span>
                                                {sampleHasMore && (
                                                    <button onClick={handleLoadMore} disabled={sampleMoreLoading}
                                                        className="rounded-lg px-3 py-1 text-xs font-medium disabled:opacity-50"
                                                        style={{ backgroundColor: "var(--accent-2)", color: "white" }}>
                                                        {sampleMoreLoading ? "Loading…" : `Load next ${SAMPLE_PAGE} rows ↓`}
                                                    </button>
                                                )}
                                                {!sampleHasMore && sampleRows.length > 0 && (
                                                    <span className="text-[10px]" style={{ color: "var(--accent-1)" }}>All loaded ✓</span>
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                    {onQuerySend && (
                        <div className="flex flex-wrap gap-2">
                            <button onClick={() => onQuerySend(`show sample data from ${selectedTable}`)}
                                className="rounded-lg px-3 py-1.5 text-xs font-medium"
                                style={{ backgroundColor: "var(--accent-1)", color: "white" }}>Query in Chat</button>
                            <button onClick={() => onQuerySend(`show row count for ${selectedTable}`)}
                                className="rounded-lg px-3 py-1.5 text-xs"
                                style={{ border: "1px solid var(--card-border)", color: "var(--foreground)", backgroundColor: "var(--tag-bg)" }}>Row Count</button>
                            <button onClick={() => onQuerySend(`show distinct values distribution for ${selectedTable}`)}
                                className="rounded-lg px-3 py-1.5 text-xs"
                                style={{ border: "1px solid var(--card-border)", color: "var(--foreground)", backgroundColor: "var(--tag-bg)" }}>Distribution</button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

// ─── Layer + schema metadata (data-driven — no hardcoded table lists) ─────────
const LAYER_META: Record<string, { label: string; color: string; description: string; icon: string }> = {
    semantic: { label: "Semantic Layer",          color: "#f59e0b", icon: "🧠", description: "Chatbot/BI-ready views — business metrics and KPI surfaces" },
    dp:       { label: "Data Products (DP)",      color: "#9b59b6", icon: "📦", description: "Domain-aligned aggregated, business-ready tables" },
    ddm:      { label: "Domain Data Model (DDM)", color: "#00A551", icon: "🏛", description: "Conformed dimensional model — typed, validated, derived fields" },
    raw:      { label: "Raw Layer",               color: "#5c9ee0", icon: "📥", description: "Ingested source records — no transformations applied" },
    audit:    { label: "Audit",                   color: "#ef4444", icon: "🔍", description: "Pipeline, data quality, and query audit logs" },
    config:   { label: "Config & Mapping",        color: "#64748b", icon: "⚙️", description: "Domain routing, intent mapping, and access control" },
    meta:     { label: "Metadata",                color: "#a78bfa", icon: "📋", description: "Dictionary, semantic catalog, and query history tables" },
};

const LAYER_ORDER = ["semantic", "dp", "ddm", "raw", "audit", "config", "meta"];

function tableGroup(name: string): string {
    if (name.startsWith("raw_"))      return "raw";
    if (name.startsWith("ddm_"))      return "ddm";
    if (name.startsWith("dp_"))       return "dp";
    if (name.startsWith("audit_"))    return "audit";
    if (name.startsWith("dic_"))      return "meta";
    if (name.startsWith("semantic_")) return "semantic";
    return "config";
}

const FACT_SUFFIXES = [
    "transaction", "payment", "statement", "pipeline_runs", "data_profile", "data_quality", "query_log",
    "transaction_enriched", "payment_status", "spend_metrics", "portfolio_kpis", "risk_signals",
    "risk_metrics", "transaction_summary", "customer_360", "balance_snapshot", "spend_monthly",
];

function tableRole(name: string): "Fact" | "Dimension" {
    const suffix = name.replace(/^[a-z]+_/, "");
    return FACT_SUFFIXES.some(s => suffix === s || suffix.startsWith(s)) ? "Fact" : "Dimension";
}

function tableLayerPrefix(name: string): string { return name.split("_")[0]; }

// ─── ERD helpers (no external graph library) ──────────────────────────────────

/** Derive FK-style join hints within a layer by matching _id column names. */
function deriveLayerJoins(layerTables: TableInfo[], allTables?: TableInfo[]): Array<{ from: string; fk: string; to: string }> {
    const inLayer = new Set(layerTables.map(t => t.name));
    const allNames = new Set((allTables ?? layerTables).map(t => t.name));
    const result: Array<{ from: string; fk: string; to: string }> = [];
    for (const table of layerTables) {
        const pfx = tableLayerPrefix(table.name);
        const pkCol = table.name.slice(pfx.length + 1) + "_id";
        for (const col of table.columns) {
            if (!col.name.endsWith("_id") || col.name === pkCol) continue;
            const entity = col.name.replace(/_id$/, "");
            // Try same-layer first, then cross-layer fallbacks
            const candidates = [
                `${pfx}_${entity}`,
                `ddm_${entity}`,
                `raw_${entity}`,
                `dp_${entity}`,
                `semantic_${entity}`,
            ];
            const target = candidates.find(c => allNames.has(c) && c !== table.name && (inLayer.has(c) || !inLayer.has(table.name + "_x")));
            if (target) result.push({ from: table.name, fk: col.name, to: target });
        }
    }
    return result;
}

function deriveAllJoins(tables: TableInfo[]): Array<{ from: string; fk: string; to: string }> {
    const allNames = new Set(tables.map(t => t.name));
    const result: Array<{ from: string; fk: string; to: string }> = [];
    for (const table of tables) {
        const pfx = tableLayerPrefix(table.name);
        const pkCol = table.name.slice(pfx.length + 1) + "_id";
        for (const col of table.columns) {
            if (!col.name.endsWith("_id") || col.name === pkCol) continue;
            const entity = col.name.replace(/_id$/, "");
            const target = [`${pfx}_${entity}`, `raw_${entity}`].find(c => allNames.has(c) && c !== table.name);
            if (target) result.push({ from: table.name, fk: col.name, to: target });
        }
    }
    return result;
}

/** Grid layout: arrange tables in rows of 3, each card 220×(60+cols*22) px. */
function gridPositions(names: string[]): Record<string, { x: number; y: number }> {
    const COLS = 3, CW = 250, RH = 240;
    return Object.fromEntries(names.map((n, i) => [n, { x: (i % COLS) * CW + 8, y: Math.floor(i / COLS) * RH + 8 }]));
}

/** Lightweight SVG-based ERD with draggable table cards. */
function NativeERD({ tables, joins, layerColor, allTables }: {
    tables: TableInfo[];
    joins: Array<{ from: string; fk: string; to: string }>;
    layerColor: string;
    allTables?: TableInfo[];
}) {
    const CARD_W = 210, CARD_HEAD = 26, ROW_H = 20, MAX_ROWS = 5;

    // Include any cross-layer targets as ghost cards
    const inLayer = useMemo(() => new Set(tables.map(t => t.name)), [tables]);
    const crossTargets = useMemo(() => {
        const extras: TableInfo[] = [];
        for (const j of joins) {
            if (!inLayer.has(j.to)) {
                const found = allTables?.find(t => t.name === j.to);
                if (found && !extras.find(e => e.name === j.to)) extras.push(found);
            }
        }
        return extras;
    }, [joins, inLayer, allTables]);
    const allDisplayTables = useMemo(() => [...tables, ...crossTargets], [tables, crossTargets]);

    // Draggable positions — reset when the table set changes
    const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});
    useEffect(() => {
        setPositions(gridPositions(allDisplayTables.map(t => t.name)));
    }, [allDisplayTables]);

    // Derived SVG canvas size from current positions
    const svgW = useMemo(() => {
        const vals = Object.values(positions);
        return Math.max(750, ...vals.map(p => p.x + CARD_W + 24));
    }, [positions]);
    const svgH = useMemo(() => {
        const vals = Object.values(positions);
        return Math.max(400, ...vals.map(p => p.y + 300));
    }, [positions]);

    // Drag state (ref so no re-render on mousemove)
    const dragRef = useRef<{ name: string; startX: number; startY: number; origX: number; origY: number } | null>(null);
    const svgRef = useRef<SVGSVGElement>(null);

    function onCardMouseDown(e: React.MouseEvent, name: string) {
        e.preventDefault();
        e.stopPropagation();
        dragRef.current = {
            name,
            startX: e.clientX, startY: e.clientY,
            origX: positions[name]?.x ?? 0,
            origY: positions[name]?.y ?? 0,
        };
    }

    function onSvgMouseMove(e: React.MouseEvent<SVGSVGElement>) {
        if (!dragRef.current) return;
        const d = dragRef.current;
        const dx = e.clientX - d.startX;
        const dy = e.clientY - d.startY;
        setPositions(prev => ({
            ...prev,
            [d.name]: { x: Math.max(0, d.origX + dx), y: Math.max(0, d.origY + dy) },
        }));
    }

    function onSvgMouseUp() { dragRef.current = null; }

    // Anchor point for FK lines (middle of card sides)
    function anchor(name: string, side: "right" | "left") {
        const pos = positions[name];
        if (!pos) return { x: 0, y: 0 };
        const shownRows = Math.min((allDisplayTables.find(t => t.name === name)?.columns.length ?? 0), MAX_ROWS);
        const h = CARD_HEAD + shownRows * ROW_H + 8;
        return { x: pos.x + (side === "right" ? CARD_W : 0), y: pos.y + h / 2 };
    }

    return (
        <div>
            <div className="flex items-center gap-2 mb-1.5">
                <button
                    onClick={() => setPositions(gridPositions(allDisplayTables.map(t => t.name)))}
                    className="rounded px-2.5 py-1 text-[10px] font-medium"
                    style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--tag-bg)", color: "var(--muted)", cursor: "pointer" }}
                    title="Reset card positions to default grid"
                >↺ Reset Layout</button>
                <span className="text-[10px]" style={{ color: "var(--muted)" }}>Drag cards to rearrange · FK lines follow</span>
            </div>
            <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 520, borderRadius: 10,
                background: "var(--panel-bg)", border: `1px solid ${layerColor}40`, userSelect: "none" }}>
                <svg ref={svgRef} width={svgW} height={svgH}
                    style={{ fontFamily: "monospace", display: "block" }}
                    onMouseMove={onSvgMouseMove}
                    onMouseUp={onSvgMouseUp}
                    onMouseLeave={onSvgMouseUp}
                >
                    <defs>
                        <marker id={`arr-${layerColor.replace("#","")}`} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                            <path d="M0,0 L0,6 L6,3 z" fill={layerColor} />
                        </marker>
                    </defs>
                    {/* FK lines — drawn below cards */}
                    {joins.map((j, i) => {
                        const from = anchor(j.from, "right");
                        const to   = anchor(j.to,   "left");
                        if (!from.x && !from.y) return null;
                        const mx   = (from.x + to.x) / 2;
                        return (
                            <g key={i}>
                                <path d={`M${from.x},${from.y} C${mx},${from.y} ${mx},${to.y} ${to.x},${to.y}`}
                                    fill="none" stroke={layerColor} strokeWidth="1.5" opacity="0.6"
                                    markerEnd={`url(#arr-${layerColor.replace("#","")})`} />
                                <text x={mx} y={(from.y + to.y) / 2 - 3}
                                    fontSize="8" fill={layerColor} opacity="0.7" textAnchor="middle">{j.fk}</text>
                            </g>
                        );
                    })}
                    {/* Table cards */}
                    {allDisplayTables.map(t => {
                        const pos = positions[t.name];
                        if (!pos) return null;
                        const isFact = tableRole(t.name) === "Fact";
                        const isGhost = !inLayer.has(t.name);
                        const accent = isGhost ? "#64748b" : (isFact ? "#1A6FE0" : "#00A551");
                        const shown  = t.columns.slice(0, MAX_ROWS);
                        const extra  = t.columns.length - shown.length;
                        const cardH  = CARD_HEAD + shown.length * ROW_H + (extra > 0 ? ROW_H : 0) + 8;
                        return (
                            <g key={t.name} transform={`translate(${pos.x},${pos.y})`}
                                opacity={isGhost ? 0.55 : 1}
                                style={{ cursor: "grab" }}
                                onMouseDown={e => onCardMouseDown(e, t.name)}>
                                <rect x={0} y={0} width={CARD_W} height={cardH} rx={7}
                                    fill="var(--card-bg)" stroke={`${accent}66`}
                                    strokeWidth={isGhost ? "1" : "1.4"}
                                    strokeDasharray={isGhost ? "4,2" : undefined} />
                                {/* Header (grab handle) */}
                                <rect x={0} y={0} width={CARD_W} height={CARD_HEAD} rx={7} fill={accent} />
                                <rect x={0} y={CARD_HEAD - 7} width={CARD_W} height={7} fill={accent} />
                                <text x={8} y={17} fontSize="10" fontWeight="bold" fill="#fff">{t.name}</text>
                                <text x={CARD_W - 20} y={17} fontSize="8" fill="rgba(255,255,255,0.7)"
                                    textAnchor="end">{isGhost ? "REF" : (isFact ? "FACT" : "DIM")}</text>
                                {/* Drag grip dots */}
                                <text x={CARD_W - 7} y={17} fontSize="9" fill="rgba(255,255,255,0.4)" textAnchor="middle">⠿</text>
                                {/* Columns */}
                                {shown.map((c, ci) => (
                                    <g key={ci} transform={`translate(0,${CARD_HEAD + ci * ROW_H})`}>
                                        <text x={8} y={14} fontSize="9" fill="rgba(255,255,255,0.78)">{c.name}</text>
                                        <text x={CARD_W - 6} y={14} fontSize="8" fill="rgba(255,255,255,0.3)"
                                            textAnchor="end">{c.type?.split("(")[0] ?? ""}</text>
                                    </g>
                                ))}
                                {extra > 0 && (
                                    <text x={8} y={CARD_HEAD + shown.length * ROW_H + 14}
                                        fontSize="8" fill="rgba(255,255,255,0.28)" fontStyle="italic">+{extra} more columns</text>
                                )}
                            </g>
                        );
                    })}
                </svg>
            </div>
        </div>
    );
}

// ─── Data Models tab ───────────────────────────────────────────────────────────
function DataModelsTab({ tables, onQuerySend }: { tables: TableInfo[]; onQuerySend?: (q: string) => void }) {
    // Groups ordered by LAYER_ORDER, only groups that have tables
    const layerGroups = useMemo(() =>
        LAYER_ORDER.filter(g => tables.some(t => tableGroup(t.name) === g)),
    [tables]);

    const [activeLayer, setActiveLayer] = useState<string>("semantic");
    // If activeLayer has no tables (e.g. after refresh), default to first available
    const effectiveLayer = layerGroups.includes(activeLayer) ? activeLayer : (layerGroups[0] ?? "semantic");

    const layerTables = useMemo(() => tables.filter(t => tableGroup(t.name) === effectiveLayer), [tables, effectiveLayer]);
    const joins        = useMemo(() => deriveLayerJoins(layerTables, tables), [layerTables, tables]);
    const layerColor   = LAYER_META[effectiveLayer]?.color ?? "#64748b";

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Entity-Relationship Diagram</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    {layerTables.length} tables · {joins.length} FK relationships
                </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
                {layerGroups.map(g => {
                    const meta  = LAYER_META[g];
                    const count = tables.filter(t => tableGroup(t.name) === g).length;
                    return (
                        <button key={g} onClick={() => setActiveLayer(g)}
                            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                            style={effectiveLayer === g
                                ? { backgroundColor: meta?.color ?? "#64748b", color: "white" }
                                : { color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
                            {meta?.icon} {meta?.label ?? g} <span style={{ opacity: 0.65 }}>({count})</span>
                        </button>
                    );
                })}
            </div>
            {layerTables.length === 0 ? (
                <div className="py-12 text-center text-sm" style={{ color: "var(--muted)" }}>No tables loaded for this layer</div>
            ) : (
                <NativeERD tables={layerTables} joins={joins} layerColor={layerColor} allTables={tables} />
            )}
            <div className="flex flex-wrap items-center gap-4 pt-0.5">
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--muted)" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: "#1A6FE0" }} />Fact
                </div>
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--muted)" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: "#00A551" }} />Dimension
                </div>
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--muted)" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: "#64748b", opacity: 0.5 }} />Cross-layer ref
                </div>
                {LAYER_META[effectiveLayer] && (
                    <span className="text-xs italic" style={{ color: "var(--muted)" }}>{LAYER_META[effectiveLayer].description}</span>
                )}
                {onQuerySend && (
                    <button onClick={() => onQuerySend(`Show summary of ${effectiveLayer} layer tables`)}
                        className="ml-auto rounded-lg px-3 py-1.5 text-xs font-medium"
                        style={{ backgroundColor: "var(--accent-1)", color: "white" }}>Explore in Chat</button>
                )}
            </div>
        </div>
    );
}

// ─── Semantic Layer tab ────────────────────────────────────────────────────────
function SemanticLayerTab({ catalog, tables = [], onQuerySend }: { catalog?: SemanticCatalogResponse | null; tables?: TableInfo[]; onQuerySend?: (q: string) => void }) {
    const [section, setSection] = useState<"metrics" | "entities" | "joins">("metrics");
    const [search, setSearch] = useState("");
    const [expandedMetric, setExpandedMetric] = useState<string | null>(null);

    const metrics = useMemo(() => {
        if (!catalog?.metrics) return [];
        const q = search.trim().toLowerCase();
        if (!q) return catalog.metrics;
        return catalog.metrics.filter(m => m.name.toLowerCase().includes(q) || m.domain.toLowerCase().includes(q) || m.definition.toLowerCase().includes(q));
    }, [catalog, search]);

    // Group tables by semantic layer for Entities section
    const layerGroups = useMemo(() => {
        const map: Record<string, TableInfo[]> = {};
        for (const t of tables) {
            const g = tableGroup(t.name);
            (map[g] = map[g] ?? []).push(t);
        }
        return map;
    }, [tables]);

    // Derive all cross-layer joins for Joins section
    const allJoins = useMemo(() => deriveAllJoins(tables), [tables]);
    const filteredJoins = useMemo(() => {
        if (!search.trim() || section !== "joins") return allJoins;
        const q = search.toLowerCase();
        return allJoins.filter(j => j.from.includes(q) || j.to.includes(q) || j.fk.includes(q));
    }, [allJoins, search, section]);

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Semantic Layer</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    {catalog?.metrics?.length ?? 0} metrics · {tables.length} tables · {allJoins.length} FK relationships
                </div>
            </div>
            <div className="flex gap-1.5">
                {(["metrics", "entities", "joins"] as const).map(s => (
                    <button key={s} onClick={() => { setSection(s); setSearch(""); }}
                        className="rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                        style={section === s
                            ? { backgroundColor: "var(--accent-2)", color: "white" }
                            : { color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
                        {s === "metrics" ? "📐 Metrics" : s === "entities" ? "🏛 Entities" : "🔗 Joins"}
                    </button>
                ))}
            </div>

            {/* ── Metrics ── */}
            {section === "metrics" && (
                <>
                    <ScbInput value={search} onChange={setSearch} placeholder="Search metrics…" />
                    {catalog?.dimensions && (
                        <div className="rounded-xl p-3" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                            <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>Global Dimensions</div>
                            <div className="flex flex-wrap gap-1.5">{catalog.dimensions.map(d => <ScbBadge key={d.name} variant="blue">{d.name}</ScbBadge>)}</div>
                        </div>
                    )}
                    <div className="space-y-2">
                        {metrics.map(metric => (
                            <div key={metric.name} className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                                <button onClick={() => setExpandedMetric(expandedMetric === metric.name ? null : metric.name)}
                                    className="flex w-full items-center justify-between px-4 py-3">
                                    <div>
                                        <div className="text-sm font-medium text-left" style={{ color: "var(--foreground)" }}>{metric.name}</div>
                                        <div className="text-[10px] text-left" style={{ color: "var(--muted)" }}>{metric.domain} · {metric.engine}</div>
                                    </div>
                                    <span style={{ color: "var(--muted)" }} className="text-xs">{expandedMetric === metric.name ? "▲" : "▼"}</span>
                                </button>
                                {expandedMetric === metric.name && (
                                    <div className="px-4 py-3 space-y-3" style={{ borderTop: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                        <div>
                                            <div className="text-[10px] font-semibold uppercase mb-1" style={{ color: "var(--muted)" }}>Definition</div>
                                            <div className="text-xs" style={{ color: "var(--foreground)" }}>{metric.definition}</div>
                                        </div>
                                        <div>
                                            <div className="text-[10px] font-semibold uppercase mb-1" style={{ color: "var(--muted)" }}>Dimensions</div>
                                            <div className="flex flex-wrap gap-1.5">{metric.dimensions.map(d => <ScbBadge key={d} variant="blue">{d}</ScbBadge>)}</div>
                                        </div>
                                        {onQuerySend && (
                                            <div className="flex gap-2">
                                                <button onClick={() => onQuerySend(`Show ${metric.name}`)}
                                                    className="rounded-lg px-3 py-1.5 text-xs font-medium"
                                                    style={{ backgroundColor: "var(--accent-1)", color: "white" }}>Query in Chat</button>
                                                <button onClick={() => onQuerySend(`Show ${metric.name} by ${metric.dimensions[0] ?? "category"}`)}
                                                    className="rounded-lg px-3 py-1.5 text-xs"
                                                    style={{ border: "1px solid var(--card-border)", color: "var(--foreground)", backgroundColor: "var(--tag-bg)" }}>
                                                    By {metric.dimensions[0] ?? "Category"}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                        {!metrics.length && <div className="py-8 text-center text-sm" style={{ color: "var(--muted)" }}>No metrics found</div>}
                    </div>
                </>
            )}

            {/* ── Entities (all tables from API, grouped by layer) ── */}
            {section === "entities" && (
                <div className="space-y-4">
                    {LAYER_ORDER.filter(g => layerGroups[g]?.length).map(g => {
                        const meta = LAYER_META[g];
                        const layerTbls = layerGroups[g];
                        return (
                            <div key={g}>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                                        style={{ background: `${meta?.color ?? "#64748b"}22`, color: meta?.color ?? "#64748b" }}>
                                        {meta?.icon} {meta?.label ?? g}
                                    </span>
                                    <span className="text-[10px]" style={{ color: "var(--muted)" }}>{layerTbls.length} tables · {meta?.description}</span>
                                </div>
                                <div className="grid gap-2 sm:grid-cols-2">
                                    {layerTbls.map(t => (
                                        <div key={t.name} className="rounded-xl p-3" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                            <div className="flex flex-wrap items-center gap-2 mb-1">
                                                <ScbBadge variant={tableRole(t.name) === "Fact" ? "blue" : "green"}>{tableRole(t.name)}</ScbBadge>
                                                <span className="text-xs font-mono font-semibold" style={{ color: "var(--foreground)" }}>{t.name}</span>
                                            </div>
                                            <div className="flex flex-wrap gap-1.5 mt-1">
                                                <ScbBadge variant="default">{t.row_count.toLocaleString()} rows</ScbBadge>
                                                <ScbBadge variant="default">{t.columns.length} cols</ScbBadge>
                                            </div>
                                            {onQuerySend && (
                                                <button onClick={() => onQuerySend(`Show summary of ${t.name}`)}
                                                    className="mt-2 rounded px-2 py-1 text-[10px]"
                                                    style={{ border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
                                                    Query ↗
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* ── Joins (auto-derived from _id FK columns) ── */}
            {section === "joins" && (
                <>
                    <ScbInput value={search} onChange={setSearch} placeholder="Filter by table or column…" />
                    <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                        <div className="px-4 py-2.5 text-xs font-semibold" style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-3)" }}>
                            {filteredJoins.length} FK relationships{search ? " (filtered)" : " — auto-derived from schema"}
                        </div>
                        <div>
                            {filteredJoins.map((j, i) => {
                                const fromColor = LAYER_META[tableGroup(j.from)]?.color ?? "#64748b";
                                const toColor   = LAYER_META[tableGroup(j.to)]?.color  ?? "#64748b";
                                return (
                                    <div key={i} className="flex flex-wrap items-center gap-2 px-4 py-2"
                                        style={{ borderTop: i > 0 ? "1px solid var(--card-border)" : undefined, backgroundColor: i % 2 ? "var(--step-bg)" : "transparent" }}>
                                        <span className="font-mono text-xs" style={{ color: fromColor }}>{j.from}</span>
                                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded" style={{ background: "var(--tag-bg)", color: "var(--muted)" }}>.{j.fk}</span>
                                        <span className="text-[10px]" style={{ color: "var(--muted)" }}>→</span>
                                        <span className="font-mono text-xs" style={{ color: toColor }}>{j.to}</span>
                                        <ScbBadge variant="default">N:1</ScbBadge>
                                    </div>
                                );
                            })}
                            {!filteredJoins.length && <div className="px-4 py-6 text-sm text-center" style={{ color: "var(--muted)" }}>No joins found</div>}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function QueryHistoryTab({ history, onQuerySend }: { history: { query: string; metric: string; rowCount: number; ts: number }[]; onQuerySend?: (q: string) => void }) {
    if (!history.length) return (
        <div className="py-12 text-center space-y-2">
            <div className="text-2xl">🕐</div>
            <div className="text-sm" style={{ color: "var(--muted)" }}>No query history yet</div>
            <div className="text-xs" style={{ color: "var(--muted)" }}>Your queries will appear here</div>
        </div>
    );
    return (
        <div className="space-y-2">
            <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Query History</div>
            {history.map((h, i) => (
                <div key={i} className="rounded-xl px-4 py-3 flex items-center justify-between gap-3"
                    style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                    <div className="min-w-0">
                        <div className="text-xs truncate" style={{ color: "var(--foreground)" }}>{h.query}</div>
                        <div className="text-[10px] mt-0.5 flex gap-2" style={{ color: "var(--muted)" }}>
                            <span>{h.metric}</span><span>·</span><span>{h.rowCount} rows</span><span>·</span>
                            <span>{new Date(h.ts).toLocaleTimeString()}</span>
                        </div>
                    </div>
                    {onQuerySend && (
                        <button onClick={() => onQuerySend(h.query)}
                            className="shrink-0 rounded px-2 py-1 text-[10px]"
                            style={{ border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>↺ Re-run</button>
                    )}
                </div>
            ))}
        </div>
    );
}

// ── Dictionary Tab ────────────────────────────────────────────────────────────

const LAYER_FILTERS: { key: string; label: string }[] = [
    { key: "all",      label: "All" },
    { key: "semantic", label: "🧠 Semantic" },
    { key: "dp",       label: "📦 Data Products" },
    { key: "ddm",      label: "🏛 DDM" },
    { key: "raw",      label: "📥 Raw" },
    { key: "audit",    label: "🔍 Audit" },
    { key: "config",   label: "⚙️ Config" },
];

function DictionaryTab({ tables: liveTables = [] }: { tables?: TableInfo[] }) {
    const [dicTables, setDicTables]       = useState<DicTable[]>([]);
    const [layer, setLayer]               = useState("all");
    const [search, setSearch]             = useState("");
    const [searchResults, setSearchResults] = useState<{ tables: DicTable[]; columns: DicColumn[] } | null>(null);
    const [expanded, setExpanded]         = useState<string | null>(null);
    const [detail, setDetail]             = useState<{ table: DicTable; columns: DicColumn[]; relationships: DicRelationship[] } | null>(null);
    const [loading, setLoading]           = useState(true);
    const [searching, setSearching]       = useState(false);
    const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        setLoading(true);
        fetchDictionaryTables(layer === "all" ? undefined : layer)
            .then(r => setDicTables(r.tables ?? []))
            .finally(() => setLoading(false));
    }, [layer]);

    // Merge live schema tables for any table not yet in dic_tables (schema-only fallback)
    const tables = useMemo(() => {
        const dicNames = new Set(dicTables.map(t => t.table_name));
        const synthetic: DicTable[] = liveTables
            .filter(t => {
                const g = tableGroup(t.name);
                return (layer === "all" || g === layer) && !dicNames.has(t.name);
            })
            .map((t, i) => ({
                table_id: -(i + 1),
                table_name: t.name,
                display_name: t.name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
                layer: tableGroup(t.name),
                domain: tableGroup(t.name),
                description: "Schema available via StarRocks DESCRIBE — no business description added yet.",
                row_count_approx: t.row_count ?? 0,
                owner: "",
                refresh_cadence: "",
            } as DicTable));
        const merged = [...dicTables, ...synthetic];
        return merged.sort((a, b) => {
            const ao = LAYER_ORDER.indexOf(a.layer ?? "config");
            const bo = LAYER_ORDER.indexOf(b.layer ?? "config");
            return ao !== bo ? ao - bo : a.table_name.localeCompare(b.table_name);
        });
    }, [dicTables, liveTables, layer]);

    // Debounced search
    useEffect(() => {
        if (searchTimeout.current) clearTimeout(searchTimeout.current);
        if (!search.trim()) { setSearchResults(null); return; }
        searchTimeout.current = setTimeout(async () => {
            setSearching(true);
            const res = await import("@/lib/api").then(m => m.searchDictionary(search));
            setSearchResults({ tables: res.tables ?? [], columns: res.columns ?? [] });
            setSearching(false);
        }, 350);
        return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
    }, [search]);

    async function handleExpand(tableName: string) {
        if (expanded === tableName) { setExpanded(null); setDetail(null); return; }
        setExpanded(tableName);
        setDetail(null);
        const res = await fetchDictionaryTableDetail(tableName);
        if (!res.error) setDetail({ table: res.table, columns: res.columns, relationships: res.relationships });
    }

    const isSchemaOnly = (t: DicTable) => (t.table_id ?? 1) < 0;

    const displayTables = searchResults
        ? searchResults.tables
        : tables;

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Data Dictionary</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    {tables.length} tables across {LAYER_ORDER.filter(g => tables.some(t => t.layer === g)).length} layers
                </div>
            </div>

            {/* Layer filter pills */}
            <div className="flex flex-wrap gap-1.5">
                {LAYER_FILTERS.map(lf => (
                    <button key={lf.key} onClick={() => { setLayer(lf.key); setSearch(""); setSearchResults(null); }}
                        className="rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-all"
                        style={layer === lf.key && !search
                            ? { backgroundColor: LAYER_META[lf.key]?.color ?? "var(--accent-2)", color: "white" }
                            : { backgroundColor: "var(--tag-bg)", color: "var(--muted)" }}>
                        {lf.label}
                    </button>
                ))}
            </div>

            {/* Search */}
            <ScbInput value={search} onChange={setSearch} placeholder="Search tables, columns, descriptions…" />
            {searching && <div className="text-xs text-center" style={{ color: "var(--muted)" }}>Searching…</div>}

            {/* Results */}
            {loading ? (
                <div className="py-8 text-center text-sm" style={{ color: "var(--muted)" }}>Loading dictionary…</div>
            ) : (
                <div className="space-y-2">
                    {displayTables.map(t => {
                        const layerMeta = LAYER_META[t.layer ?? "config"];
                        return (
                            <div key={t.table_name} className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                                <button onClick={() => handleExpand(t.table_name)}
                                    className="flex w-full items-center justify-between px-4 py-3 text-left">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <span className="text-base shrink-0">{layerMeta?.icon ?? "📖"}</span>
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2">
                                                <div className="text-sm font-medium" style={{ color: "var(--foreground)" }}>{t.display_name || t.table_name}</div>
                                                {isSchemaOnly(t) && <ScbBadge variant="amber">schema only</ScbBadge>}
                                            </div>
                                            <div className="text-xs font-mono mt-0.5" style={{ color: "var(--accent-2)" }}>{t.table_name}</div>
                                            {t.description && (
                                                <div className="text-[11px] mt-0.5 truncate" style={{ color: "var(--muted)" }}>{t.description}</div>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0 ml-2">
                                        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                                            style={{ background: `${layerMeta?.color ?? "#64748b"}22`, color: layerMeta?.color ?? "#64748b" }}>
                                            {layerMeta?.label ?? t.layer}
                                        </span>
                                        <span className="text-xs" style={{ color: "var(--muted)" }}>{expanded === t.table_name ? "▲" : "▼"}</span>
                                    </div>
                                </button>

                                {expanded === t.table_name && (
                                    <div className="px-4 py-3 space-y-3" style={{ borderTop: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                        {/* Stats row */}
                                        <div className="flex flex-wrap gap-3">
                                            {t.domain     && <ScbBadge variant="default">Domain: {t.domain}</ScbBadge>}
                                            {t.owner      && <ScbBadge variant="default">Owner: {t.owner}</ScbBadge>}
                                            {t.row_count_approx !== undefined && t.row_count_approx > 0 && (
                                                <ScbBadge variant="green">{t.row_count_approx.toLocaleString()} rows</ScbBadge>
                                            )}
                                            {t.refresh_cadence && <ScbBadge variant="blue">Refresh: {t.refresh_cadence}</ScbBadge>}
                                        </div>

                                        {/* Columns */}
                                        {detail ? (
                                            <>
                                                {detail.columns.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: "var(--muted)" }}>Columns</div>
                                                        <div className="overflow-x-auto">
                                                            <table className="w-full text-xs">
                                                                <thead>
                                                                    <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--muted)" }}>
                                                                        <th className="pb-1.5 text-left font-medium pr-4">Column</th>
                                                                        <th className="pb-1.5 text-left font-medium pr-4">Type</th>
                                                                        <th className="pb-1.5 text-left font-medium">Description</th>
                                                                    </tr>
                                                                </thead>
                                                                <tbody>
                                                                    {detail.columns.map((c, i) => (
                                                                        <tr key={i} style={{ borderBottom: "1px solid var(--card-border)" }}>
                                                                            <td className="py-1.5 pr-4 font-mono" style={{ color: "var(--foreground)" }}>
                                                                                {c.is_primary_key ? <ScbBadge variant="amber">PK</ScbBadge> : null}
                                                                                {" "}{c.column_name}
                                                                            </td>
                                                                            <td className="py-1.5 pr-4 font-mono" style={{ color: "var(--accent-3)" }}>{c.data_type}</td>
                                                                            <td className="py-1.5 text-[10px]" style={{ color: "var(--muted)" }}>{c.description ?? "—"}</td>
                                                                        </tr>
                                                                    ))}
                                                                </tbody>
                                                            </table>
                                                        </div>
                                                    </div>
                                                )}
                                                {detail.relationships.length > 0 && (
                                                    <div>
                                                        <div className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: "var(--muted)" }}>Relationships</div>
                                                        <div className="space-y-1">
                                                            {detail.relationships.map((r, i) => (
                                                                <div key={i} className="text-xs flex items-center gap-2" style={{ color: "var(--muted)" }}>
                                                                    <span className="font-mono" style={{ color: "var(--accent-2)" }}>{r.from_table}.{r.from_column}</span>
                                                                    <span>→</span>
                                                                    <span className="font-mono" style={{ color: "var(--accent-1)" }}>{r.to_table}.{r.to_column}</span>
                                                                    <ScbBadge variant="default">{r.relationship_type ?? "FK"}</ScbBadge>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        ) : (
                                            <div className="text-xs" style={{ color: "var(--muted)" }}>Loading details…</div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    {!displayTables.length && (
                        <div className="py-8 text-center text-sm" style={{ color: "var(--muted)" }}>
                            {search ? "No matches found" : "No tables in dictionary"}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export function ExplorerPanel({ catalog, tables = [], database = "cc_analytics", queryHistory = [], onQuerySend, onRefreshTables, tablesLoading }: ExplorerPanelProps) {
    const [activeTab, setActiveTab] = useState<ExplorerTab>("datasets");
    return (
        <div className="space-y-4">
            <div className="rounded-2xl p-4" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>Data Explorer</div>
                        <div className="mt-0.5 text-xs" style={{ color: "var(--muted)" }}>Browse datasets, profiling, data models, semantic layer, dictionary and history</div>
                    </div>
                    {onRefreshTables && (
                        <button onClick={onRefreshTables} disabled={tablesLoading}
                            className="rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-50"
                            style={{ border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
                            {tablesLoading ? "Loading…" : "↺ Refresh"}
                        </button>
                    )}
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                    <ScbTabBtn active={activeTab === "datasets"}   onClick={() => setActiveTab("datasets")}>🗄 Tables</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "profiling"}  onClick={() => setActiveTab("profiling")}>📊 Profiling</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "models"}     onClick={() => setActiveTab("models")}>🔗 Models</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "semantic"}   onClick={() => setActiveTab("semantic")}>🧠 Semantic</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "dictionary"} onClick={() => setActiveTab("dictionary")}>📖 Dictionary</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "history"}    onClick={() => setActiveTab("history")}>
                        🕐 History{queryHistory.length > 0 ? ` (${queryHistory.length})` : ""}
                    </ScbTabBtn>
                </div>
            </div>
            <div>
                {activeTab === "datasets"   && <DatasetsTab  tables={tables} database={database} />}
                {activeTab === "profiling"  && <ProfilingTab tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "models"     && <DataModelsTab tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "semantic"   && <SemanticLayerTab catalog={catalog} tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "dictionary" && <DictionaryTab tables={tables} />}
                {activeTab === "history"    && <QueryHistoryTab history={queryHistory} onQuerySend={onQuerySend} />}
            </div>
        </div>
    );
}
