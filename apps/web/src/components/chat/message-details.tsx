"use client";

import { useState } from "react";
import { ChatMessage } from "@/types/chat";

type MessageDetailsProps = {
    message: ChatMessage;
};

function DetailSection({
    title,
    children,
}: {
    title: string;
    children: React.ReactNode;
}) {
    const [open, setOpen] = useState(false);

    return (
        <div className="rounded-xl border border-zinc-800 bg-zinc-950">
            <button
                onClick={() => setOpen((v) => !v)}
                className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-zinc-200"
            >
                <span>{title}</span>
                <span className="text-zinc-500">{open ? "−" : "+"}</span>
            </button>
            {open && <div className="border-t border-zinc-800 px-4 py-4">{children}</div>}
        </div>
    );
}

export function MessageDetails({ message }: MessageDetailsProps) {
    const hasDetails =
        message.sql ||
        message.assumptions?.length ||
        message.semanticContext ||
        message.resultRows?.length;

    if (!hasDetails) return null;

    return (
        <div className="mt-4 space-y-3">
            {message.sql && (
                <DetailSection title="SQL">
                    <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-300">
                        {message.sql}
                    </pre>

                    {message.sqlExplanation && (
                        <div className="mt-4">
                            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                                Explanation
                            </div>
                            <div className="text-sm text-zinc-300">{message.sqlExplanation}</div>
                        </div>
                    )}

                    {message.sqlValidationIssues?.length ? (
                        <div className="mt-4">
                            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                                Validation Notes
                            </div>
                            <ul className="space-y-1 text-sm text-zinc-300">
                                {message.sqlValidationIssues.map((item) => (
                                    <li key={item}>• {item}</li>
                                ))}
                            </ul>
                        </div>
                    ) : null}
                </DetailSection>
            )}

            {message.assumptions?.length ? (
                <DetailSection title="Assumptions">
                    <ul className="space-y-2 text-sm text-zinc-300">
                        {message.assumptions.map((item) => (
                            <li key={item}>• {item}</li>
                        ))}
                    </ul>
                </DetailSection>
            ) : null}

            {message.semanticContext ? (
                <DetailSection title="Semantic Context">
                    <div className="space-y-2 text-sm text-zinc-300">
                        <div>
                            <span className="text-zinc-500">Domain:</span>{" "}
                            {message.semanticContext.domain || "N/A"}
                        </div>
                        <div>
                            <span className="text-zinc-500">Metric:</span>{" "}
                            {message.semanticContext.metric || "N/A"}
                        </div>
                        <div>
                            <span className="text-zinc-500">Definition:</span>{" "}
                            {message.semanticContext.definition || "N/A"}
                        </div>
                        <div>
                            <span className="text-zinc-500">Dimensions:</span>{" "}
                            {message.semanticContext.dimensions?.join(", ") || "N/A"}
                        </div>
                        <div>
                            <span className="text-zinc-500">Engine:</span>{" "}
                            {message.semanticContext.engine || "N/A"}
                        </div>
                    </div>
                </DetailSection>
            ) : null}

            {message.resultRows?.length && message.resultColumns?.length ? (
                <DetailSection title="Result Preview">
                    <div className="mb-3 text-xs text-zinc-500">
                        Engine: {message.resultEngine || "N/A"} · Rows: {message.resultRowCount ?? 0}
                        {" · "}
                        Time: {message.resultExecutionTimeMs ?? 0} ms
                    </div>
                    <div className="overflow-x-auto">
                        <table className="min-w-full text-left text-xs text-zinc-300">
                            <thead>
                                <tr className="border-b border-zinc-800 text-zinc-500">
                                    {message.resultColumns.map((column) => (
                                        <th key={column} className="px-2 py-2 font-medium">
                                            {column}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {message.resultRows.slice(0, 5).map((row, idx) => (
                                    <tr key={idx} className="border-b border-zinc-900">
                                        {message.resultColumns?.map((column) => (
                                            <td key={column} className="px-2 py-2">
                                                {String(row[column] ?? "")}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </DetailSection>
            ) : null}
        </div>
    );
}
