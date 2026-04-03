import { AnalysisState } from "@/types/chat";

type AnalysisTabsProps = {
  analysis: AnalysisState;
};

function formatPersona(persona?: string) {
  if (!persona) return "N/A";
  const map: Record<string, string> = {
    analyst: "Analyst",
    cfo: "CFO",
    manager: "Manager",
    product: "Product",
    engineer: "Engineer",
  };
  return map[persona] || persona;
}

export function AnalysisTabs({ analysis }: AnalysisTabsProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-800 px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {["Chart", "SQL", "Insights", "Semantic", "Lineage"].map((tab) => (
            <button
              key={tab}
              className={`rounded-full px-3 py-1.5 text-xs ${tab === "Chart"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4 overflow-y-auto p-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-3 text-sm font-semibold">Chart Preview</div>
          <div className="mb-3 text-xs text-zinc-500">
            {analysis.chartTitle || "No chart yet"} · {analysis.chartType || "N/A"}
          </div>
          <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-500">
            Chart rendering comes next
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">SQL</div>
          <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-300">
            {analysis.sql || "No SQL yet"}
          </pre>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Insights</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {(analysis.insights || ["No insights yet"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Assumptions</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {(analysis.assumptions || ["No assumptions yet"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Semantic Context</div>
          <div className="space-y-2 text-sm text-zinc-300">
            <div>
              <span className="text-zinc-500">Domain:</span>{" "}
              {analysis.semanticContext?.domain || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Metric:</span>{" "}
              {analysis.semanticContext?.metric || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Definition:</span>{" "}
              {analysis.semanticContext?.definition || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Dimensions:</span>{" "}
              {analysis.semanticContext?.dimensions?.join(", ") || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Engine:</span>{" "}
              {analysis.semanticContext?.engine || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Persona:</span>{" "}
              {formatPersona(analysis.semanticContext?.persona)}
            </div>
            <div>
              <span className="text-zinc-500">Template:</span>{" "}
              {analysis.semanticContext?.promptTemplateLoaded || "N/A"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
