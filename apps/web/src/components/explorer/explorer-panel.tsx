"use client";

import { useMemo, useState } from "react";
import { SemanticCatalogResponse } from "@/types/chat";

type ExplorerPanelProps = {
  catalog?: SemanticCatalogResponse | null;
};

export function ExplorerPanel({ catalog }: ExplorerPanelProps) {
  const [query, setQuery] = useState("");

  const filteredMetrics = useMemo(() => {
    if (!catalog?.metrics) return [];
    const q = query.trim().toLowerCase();
    if (!q) return catalog.metrics;

    return catalog.metrics.filter((metric) => {
      return (
        metric.name.toLowerCase().includes(q) ||
        metric.domain.toLowerCase().includes(q) ||
        metric.definition.toLowerCase().includes(q) ||
        metric.keywords.some((k) => k.toLowerCase().includes(q))
      );
    });
  }, [catalog, query]);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
        <div className="mb-3 text-lg font-semibold">Data Explorer</div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search metrics, domains, definitions..."
          className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
        />
      </div>

      <div className="grid gap-4">
        {filteredMetrics.map((metric) => (
          <div
            key={metric.name}
            className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-base font-semibold">{metric.name}</div>
                <div className="mt-1 text-xs text-zinc-500">
                  Domain: {metric.domain} · Engine: {metric.engine}
                </div>
              </div>
              <div className="rounded-full bg-zinc-950 px-3 py-1 text-xs text-zinc-400">
                {metric.engine}
              </div>
            </div>

            <div className="mt-3 text-sm text-zinc-300">{metric.definition}</div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-medium text-zinc-500">
                Dimensions
              </div>
              <div className="flex flex-wrap gap-2">
                {metric.dimensions.map((dimension) => (
                  <span
                    key={dimension}
                    className="rounded-full bg-zinc-950 px-3 py-1 text-xs text-zinc-300"
                  >
                    {dimension}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-4">
              <div className="mb-2 text-xs font-medium text-zinc-500">
                Keywords
              </div>
              <div className="flex flex-wrap gap-2">
                {metric.keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-400"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}

        {!filteredMetrics.length && (
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 text-sm text-zinc-500">
            No matching metrics found.
          </div>
        )}
      </div>
    </div>
  );
}