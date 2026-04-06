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
import { TableInfo, fetchTableSample } from "@/lib/api";

type ExplorerTab = "datasets" | "profiling" | "models" | "semantic" | "history";

type ExplorerPanelProps = {
    catalog?: SemanticCatalogResponse | null;
    tables?: TableInfo[];
    database?: string;
    queryHistory?: { query: string; metric: string; rowCount: number; ts: number }[];
    onQuerySend?: (query: string) => void;
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



function DatasetsTab({ tables, database }: { tables: TableInfo[]; database: string }) {
    const [expanded, setExpanded] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    const filtered = tables.filter(t => !search || t.name.toLowerCase().includes(search.toLowerCase()));
    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Tables</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    DB: <span style={{ color: "var(--accent-2)" }}>{database}</span> · {tables.length} tables
                </div>
            </div>
            <ScbInput value={search} onChange={setSearch} placeholder="Search tables..." />
            <div className="space-y-2">
                {filtered.map(t => (
                    <div key={t.name} className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                        <button onClick={() => setExpanded(expanded === t.name ? null : t.name)}
                            className="flex w-full items-center justify-between px-4 py-3">
                            <div className="flex items-center gap-3">
                                <span>🗃</span>
                                <div>
                                    <div className="text-sm font-medium" style={{ color: "var(--foreground)" }}>{t.name}</div>
                                    <div className="text-xs" style={{ color: "var(--muted)" }}>{t.columns.length} columns</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <ScbBadge variant="green">{t.row_count.toLocaleString()} rows</ScbBadge>
                                <span style={{ color: "var(--muted)" }} className="text-xs">{expanded === t.name ? "▲" : "▼"}</span>
                            </div>
                        </button>
                        {expanded === t.name && (
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
                ))}
                {!filtered.length && <div className="py-8 text-center text-sm" style={{ color: "var(--muted)" }}>{tables.length === 0 ? "Loading tables…" : "No tables found"}</div>}
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
    const table = tables.find(t => t.name === selectedTable);

    useEffect(() => {
        setSampleOpen(false);
        setSampleRows([]);
        setSampleHasMore(false);
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

    return (
        <div className="space-y-4">
            <div>
                <div className="text-sm font-semibold mb-2" style={{ color: "var(--foreground)" }}>Data Profiling</div>
                <select value={selectedTable} onChange={e => setSelectedTable(e.target.value)}
                    className="w-full rounded-lg px-3 py-2 text-sm cursor-pointer"
                    style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--tag-bg)", color: "var(--foreground)" }}>
                    {tables.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                </select>
            </div>
            {table && (
                <>
                    <div className="grid grid-cols-3 gap-3">
                        {([
                            { label: "Total Rows", value: table.row_count.toLocaleString(), color: "var(--accent-1)" },
                            { label: "Columns", value: table.columns.length.toString(), color: "var(--accent-2)" },
                            { label: "Nullable Cols", value: table.columns.filter(c => c.nullable === "YES").length.toString(), color: "#f59e0b" },
                        ] as { label: string; value: string; color: string }[]).map(k => (
                            <div key={k.label} className="rounded-xl p-3 text-center" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)" }}>
                                <div className="text-[10px] uppercase tracking-wide mb-1" style={{ color: "var(--muted)" }}>{k.label}</div>
                                <div className="text-lg font-bold" style={{ color: k.color }}>{k.value}</div>
                            </div>
                        ))}
                    </div>
                    <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--card-border)" }}>
                        <div className="px-4 py-2.5 text-xs font-semibold" style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-3)" }}>Column Profile</div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                                <thead>
                                    <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--muted)" }}>
                                        <th className="px-3 py-2 text-left font-medium">Column</th>
                                        <th className="px-3 py-2 text-left font-medium">Type</th>
                                        <th className="px-3 py-2 text-right font-medium">Nullable</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table.columns.map((c, i) => (
                                        <tr key={i} style={{ borderBottom: "1px solid var(--card-border)", backgroundColor: i % 2 ? "var(--step-bg)" : "transparent" }}>
                                            <td className="px-3 py-1.5 font-mono" style={{ color: "var(--foreground)" }}>{c.name}</td>
                                            <td className="px-3 py-1.5 font-mono" style={{ color: "var(--accent-3)" }}>{c.type}</td>
                                            <td className="px-3 py-1.5 text-right" style={{ color: "var(--muted)" }}>{c.nullable === "YES" ? "Yes" : "No"}</td>
                                        </tr>
                                    ))}
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
const LAYER_META: Record<string, { label: string; color: string; description: string }> = {
    raw:      { label: "Raw",      color: "#5c9ee0", description: "Ingested source records — no transformations applied" },
    ddm:      { label: "DDM",      color: "#00A551", description: "Dimensional Data Model — conformed and typed layer" },
    dp:       { label: "DP",       color: "#9b59b6", description: "Data Products — aggregated business-ready views" },
    semantic: { label: "Semantic", color: "#f59e0b", description: "Semantic views — business metrics and KPI surfaces" },
    audit:    { label: "Audit",    color: "#ef4444", description: "Pipeline, quality, and query audit logs" },
    domain:   { label: "Config",   color: "#64748b", description: "Domain, intent, and access configuration tables" },
    intent:   { label: "Config",   color: "#64748b", description: "Intent and domain configuration" },
    user:     { label: "Config",   color: "#64748b", description: "User access role mapping" },
};

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
function deriveLayerJoins(layerTables: TableInfo[]): Array<{ from: string; fk: string; to: string }> {
    const inLayer = new Set(layerTables.map(t => t.name));
    const result: Array<{ from: string; fk: string; to: string }> = [];
    for (const table of layerTables) {
        const pfx = tableLayerPrefix(table.name);
        const pkCol = table.name.slice(pfx.length + 1) + "_id";
        for (const col of table.columns) {
            if (!col.name.endsWith("_id") || col.name === pkCol) continue;
            const target = `${pfx}_${col.name.replace(/_id$/, "")}`;
            if (inLayer.has(target) && target !== table.name)
                result.push({ from: table.name, fk: col.name, to: target });
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

/** Lightweight SVG-based ERD — no external library required. */
function NativeERD({ tables, joins, layerColor }: {
    tables: TableInfo[];
    joins: Array<{ from: string; fk: string; to: string }>;
    layerColor: string;
}) {
    const CARD_W = 210, CARD_HEAD = 26, ROW_H = 20, COLS = 3, COL_W = 250, MAX_ROWS = 5;
    const positions = useMemo(() => gridPositions(tables.map(t => t.name)), [tables]);
    const svgW = Math.max(COLS * COL_W + 16, 700);
    const rowCount = Math.ceil(tables.length / COLS);
    const svgH = rowCount * 240 + 24;

    // Midpoint of a card's right edge for a given table
    function anchor(name: string, side: "right" | "left") {
        const pos = positions[name];
        if (!pos) return { x: 0, y: 0 };
        const shownRows = Math.min((tables.find(t => t.name === name)?.columns.length ?? 0), MAX_ROWS);
        const h = CARD_HEAD + shownRows * ROW_H + 8;
        return { x: pos.x + (side === "right" ? CARD_W : 0), y: pos.y + h / 2 };
    }

    const svgRef = useRef<SVGSVGElement>(null);

    return (
        <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 500, borderRadius: 10,
            background: "var(--panel-bg)", border: `1px solid ${layerColor}40` }}>
            <svg ref={svgRef} width={svgW} height={svgH} style={{ fontFamily: "monospace" }}>
                <defs>
                    <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                        <path d="M0,0 L0,6 L6,3 z" fill={layerColor} />
                    </marker>
                </defs>
                {/* FK lines */}
                {joins.map((j, i) => {
                    const from = anchor(j.from, "right");
                    const to   = anchor(j.to,   "left");
                    const mx   = (from.x + to.x) / 2;
                    return (
                        <g key={i}>
                            <path d={`M${from.x},${from.y} C${mx},${from.y} ${mx},${to.y} ${to.x},${to.y}`}
                                fill="none" stroke={layerColor} strokeWidth="1.2" opacity="0.55"
                                markerEnd="url(#arr)" />
                            <text x={mx} y={(from.y + to.y) / 2 - 3}
                                fontSize="8" fill={layerColor} opacity="0.6" textAnchor="middle">{j.fk}</text>
                        </g>
                    );
                })}
                {/* Table cards */}
                {tables.map(t => {
                    const pos = positions[t.name];
                    if (!pos) return null;
                    const isFact = tableRole(t.name) === "Fact";
                    const accent = isFact ? "#1A6FE0" : "#00A551";
                    const shown  = t.columns.slice(0, MAX_ROWS);
                    const extra  = t.columns.length - shown.length;
                    const cardH  = CARD_HEAD + shown.length * ROW_H + (extra > 0 ? ROW_H : 0) + 8;
                    return (
                        <g key={t.name} transform={`translate(${pos.x},${pos.y})`}>
                            <rect x={0} y={0} width={CARD_W} height={cardH} rx={7}
                                fill="var(--card-bg)" stroke={`${accent}66`} strokeWidth="1.4" />
                            {/* Header */}
                            <rect x={0} y={0} width={CARD_W} height={CARD_HEAD} rx={7} fill={accent} />
                            <rect x={0} y={CARD_HEAD - 7} width={CARD_W} height={7} fill={accent} />
                            <text x={8} y={17} fontSize="10" fontWeight="bold" fill="#fff">{t.name}</text>
                            <text x={CARD_W - 6} y={17} fontSize="8" fill="rgba(255,255,255,0.7)"
                                textAnchor="end">{isFact ? "FACT" : "DIM"}</text>
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
    );
}

// ─── Data Models tab ───────────────────────────────────────────────────────────
function DataModelsTab({ tables, onQuerySend }: { tables: TableInfo[]; onQuerySend?: (q: string) => void }) {
    const layerGroups = useMemo(() => {
        const seen = new Set<string>(); const groups: string[] = [];
        for (const t of tables) { const p = tableLayerPrefix(t.name); if (!seen.has(p)) { seen.add(p); groups.push(p); } }
        return groups;
    }, [tables]);

    const [activeLayer, setActiveLayer] = useState<string>(() => layerGroups[0] ?? "raw");

    const layerTables = useMemo(() => tables.filter(t => tableLayerPrefix(t.name) === activeLayer), [tables, activeLayer]);
    const joins        = useMemo(() => deriveLayerJoins(layerTables), [layerTables]);
    const layerColor   = LAYER_META[activeLayer]?.color ?? "#64748b";

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>Entity-Relationship Diagram</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                    {layerTables.length} tables · {joins.length} FK relationships
                </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
                {layerGroups.map(p => {
                    const meta = LAYER_META[p];
                    const count = tables.filter(t => tableLayerPrefix(t.name) === p).length;
                    return (
                        <button key={p} onClick={() => setActiveLayer(p)}
                            className="rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                            style={activeLayer === p
                                ? { backgroundColor: meta?.color ?? "#64748b", color: "white" }
                                : { color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}>
                            {meta?.label ?? p} <span style={{ opacity: 0.65 }}>({count})</span>
                        </button>
                    );
                })}
            </div>
            {layerTables.length === 0 ? (
                <div className="py-12 text-center text-sm" style={{ color: "var(--muted)" }}>No tables loaded for this layer</div>
            ) : (
                <NativeERD tables={layerTables} joins={joins} layerColor={layerColor} />
            )}
            <div className="flex flex-wrap items-center gap-4 pt-0.5">
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--muted)" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: "#1A6FE0" }} />Fact
                </div>
                <div className="flex items-center gap-1.5 text-xs" style={{ color: "var(--muted)" }}>
                    <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: 2, background: "#00A551" }} />Dimension
                </div>
                {LAYER_META[activeLayer] && (
                    <span className="text-xs italic" style={{ color: "var(--muted)" }}>{LAYER_META[activeLayer].description}</span>
                )}
                {onQuerySend && (
                    <button onClick={() => onQuerySend(`Show summary of ${activeLayer} layer tables`)}
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

    // Group tables by layer for Entities section
    const layerGroups = useMemo(() => {
        const map: Record<string, TableInfo[]> = {};
        for (const t of tables) {
            const p = tableLayerPrefix(t.name);
            (map[p] = map[p] ?? []).push(t);
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
                    {Object.entries(layerGroups).map(([prefix, layerTbls]) => {
                        const meta = LAYER_META[prefix];
                        return (
                            <div key={prefix}>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
                                        style={{ background: `${meta?.color ?? "#64748b"}22`, color: meta?.color ?? "#64748b" }}>
                                        {meta?.label ?? prefix}
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
                                const fromPfx = tableLayerPrefix(j.from);
                                const toPfx   = tableLayerPrefix(j.to);
                                const fromColor = LAYER_META[fromPfx]?.color ?? "#64748b";
                                const toColor   = LAYER_META[toPfx]?.color  ?? "#64748b";
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

export function ExplorerPanel({ catalog, tables = [], database = "cc_analytics", queryHistory = [], onQuerySend }: ExplorerPanelProps) {
    const [activeTab, setActiveTab] = useState<ExplorerTab>("datasets");
    return (
        <div className="space-y-4">
            <div className="rounded-2xl p-4" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
                <div className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>Data Explorer</div>
                <div className="mt-0.5 text-xs" style={{ color: "var(--muted)" }}>Browse datasets, profiling, data models, semantic layer, and history</div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                    <ScbTabBtn active={activeTab === "datasets"} onClick={() => setActiveTab("datasets")}>🗄 Tables</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "profiling"} onClick={() => setActiveTab("profiling")}>📊 Profiling</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "models"} onClick={() => setActiveTab("models")}>🔗 Models</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "semantic"} onClick={() => setActiveTab("semantic")}>🧠 Semantic</ScbTabBtn>
                    <ScbTabBtn active={activeTab === "history"} onClick={() => setActiveTab("history")}>
                        🕐 History{queryHistory.length > 0 ? ` (${queryHistory.length})` : ""}
                    </ScbTabBtn>
                </div>
            </div>
            <div>
                {activeTab === "datasets" && <DatasetsTab tables={tables} database={database} />}
                {activeTab === "profiling" && <ProfilingTab tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "models" && <DataModelsTab tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "semantic" && <SemanticLayerTab catalog={catalog} tables={tables} onQuerySend={onQuerySend} />}
                {activeTab === "history" && <QueryHistoryTab history={queryHistory} onQuerySend={onQuerySend} />}
            </div>
        </div>
    );
}
