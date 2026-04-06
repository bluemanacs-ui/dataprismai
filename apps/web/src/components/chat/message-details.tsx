"use client";

import { useState } from "react";
import { ChatMessage } from "@/types/chat";

type MessageDetailsProps = {
    message: ChatMessage;
};

function downloadText(filename: string, content: string, mime = "text/plain") {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([content], { type: mime }));
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
}

function DownloadBtn({ label, onClick }: { label: string; onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--step-bg)", color: "var(--foreground)" }}
            className="flex items-center gap-1 rounded px-2 py-1 text-[10px] hover:opacity-80"
        >
            ↓ {label}
        </button>
    );
}

function DetailSection({
    title,
    icon = "",
    accentBorder = "var(--card-border)",
    accentBg = "var(--step-bg)",
    accentText = "var(--foreground)",
    children,
    actions,
    defaultOpen = false,
}: {
    title: string;
    icon?: string;
    accentBorder?: string;
    accentBg?: string;
    accentText?: string;
    children: React.ReactNode;
    actions?: React.ReactNode;
    defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);

    return (
        <div className="rounded-xl overflow-hidden" style={{ border: `1px solid ${accentBorder}` }}>
            <button
                onClick={() => setOpen((v) => !v)}
                className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-semibold"
                style={{ backgroundColor: accentBg, color: accentText }}
            >
                <span className="flex items-center gap-2">
                    {icon && <span>{icon}</span>}
                    {title}
                </span>
                <span style={{ color: "var(--muted)" }}>{open ? "▲" : "▼"}</span>
            </button>
            {open && (
                <div style={{ borderTop: `1px solid ${accentBorder}`, backgroundColor: "var(--step-bg)" }} className="px-4 py-4">
                    {actions && <div className="mb-3 flex flex-wrap gap-2">{actions}</div>}
                    {children}
                </div>
            )}
        </div>
    );
}

const PAGE_SIZE = 20;

function ResultTable({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
    const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
    const visible = rows.slice(0, visibleCount);
    const remaining = rows.length - visibleCount;
    const loadMore = () => setVisibleCount((n) => n + PAGE_SIZE);

    return (
        <>
            <div className="overflow-x-auto">
                <table className="min-w-full text-left text-xs" style={{ color: "var(--foreground)" }}>
                    <thead>
                        <tr style={{ borderBottom: "1px solid var(--card-border)", color: "var(--muted)" }}>
                            {columns.map((column) => (
                                <th key={column} className="px-2 py-2 font-semibold">
                                    {column}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {visible.map((row, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid var(--card-border)" }}
                                className="hover:opacity-80">
                                {columns.map((column) => (
                                    <td key={column} className="px-2 py-2">
                                        {String(row[column] ?? "")}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {remaining > 0 && (
                <div className="mt-2 flex items-center justify-between">
                    <span className="text-[10px]" style={{ color: "var(--muted)" }}>
                        Showing {visible.length} of {rows.length} rows
                    </span>
                    <button
                        onClick={loadMore}
                        className="rounded-lg px-3 py-1 text-[10px] font-semibold transition-opacity hover:opacity-80"
                        style={{
                            border: "1px solid rgba(0,165,81,0.4)",
                            backgroundColor: "rgba(0,165,81,0.08)",
                            color: "var(--accent-1)",
                        }}
                    >
                        Load {Math.min(remaining, PAGE_SIZE)} more ›
                    </button>
                </div>
            )}
            {remaining <= 0 && rows.length > PAGE_SIZE && (
                <div className="mt-1 text-right text-[10px]" style={{ color: "var(--muted)" }}>
                    All {rows.length} rows shown
                </div>
            )}
        </>
    );
}

export function MessageDetails({ message }: MessageDetailsProps) {
    const hasDetails =
        message.sql ||
        message.semanticContext ||
        message.resultRows?.length;

    if (!hasDetails) return null;

    return (
        <div className="mt-4 space-y-2">
            {message.sql && (
                <DetailSection
                    title="SQL"
                    icon="⚙"
                    accentBorder="rgba(0,212,255,0.3)"
                    accentBg="rgba(0,212,255,0.06)"
                    accentText="var(--accent-3)"
                    actions={
                        <DownloadBtn label="Download SQL" onClick={() =>
                            downloadText("query.sql", message.sql ?? "", "text/plain")
                        } />
                    }
                >
                    <pre className="overflow-x-auto whitespace-pre-wrap text-xs" style={{ color: "var(--accent-3)", fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)" }}>
                        {message.sql}
                    </pre>

                    {message.sqlExplanation && (
                        <div className="mt-4">
                            <div className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                                Explanation
                            </div>
                            <div className="text-sm" style={{ color: "var(--foreground)" }}>{message.sqlExplanation}</div>
                        </div>
                    )}

                    {message.sqlValidationIssues?.length ? (
                        <div className="mt-4">
                            <div className="mb-2 text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                                Validation Notes
                            </div>
                            <ul className="space-y-1 text-sm" style={{ color: "var(--foreground)" }}>
                                {message.sqlValidationIssues.map((item) => (
                                    <li key={item}>• {item}</li>
                                ))}
                            </ul>
                        </div>
                    ) : null}
                </DetailSection>
            )}

            {message.semanticContext ? (
                <DetailSection title="Semantic Context" icon="📌"
                    accentBorder="rgba(26,111,224,0.35)"
                    accentBg="rgba(26,111,224,0.08)"
                    accentText="var(--accent-2)">
                    <div className="space-y-2 text-sm" style={{ color: "var(--foreground)" }}>
                        {[
                            ["Domain", message.semanticContext.domain],
                            ["Metric", message.semanticContext.metric],
                            ["Definition", message.semanticContext.definition],
                            ["Dimensions", message.semanticContext.dimensions?.join(", ")],
                            ["Engine", message.semanticContext.engine],
                        ].map(([label, val]) => val ? (
                            <div key={label as string}>
                                <span style={{ color: "var(--muted)" }}>{label}:</span>{" "}
                                {val}
                            </div>
                        ) : null)}
                    </div>
                </DetailSection>
            ) : null}

            {message.resultRows?.length && message.resultColumns?.length ? (
                <DetailSection
                    title="Result Preview"
                    icon="📋"
                    accentBorder="rgba(0,165,81,0.3)"
                    accentBg="rgba(0,165,81,0.06)"
                    accentText="var(--accent-1)"
                    defaultOpen={false}
                    actions={<>
                        <DownloadBtn label="CSV" onClick={() => {
                            const cols = message.resultColumns ?? [];
                            const rows = message.resultRows ?? [];
                            const csv = [cols.join(","), ...rows.map(r => cols.map(c => JSON.stringify(r[c] ?? "")).join(","))].join("\n");
                            downloadText("results.csv", csv, "text/csv");
                        }} />
                        <DownloadBtn label="JSON" onClick={() =>
                            downloadText("results.json", JSON.stringify(message.resultRows, null, 2), "application/json")
                        } />
                    </>}
                >
                    <div className="mb-3 text-xs" style={{ color: "var(--muted)" }}>
                        Engine: {message.resultEngine || "N/A"} · Rows: {message.resultRowCount ?? 0} · Time: {message.resultExecutionTimeMs ?? 0} ms
                    </div>
                    <ResultTable rows={message.resultRows} columns={message.resultColumns} />
                </DetailSection>
            ) : null}
        </div>
    );
}
