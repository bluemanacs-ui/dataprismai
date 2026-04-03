export function AnalysisTabs() {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-800 px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {["Chart", "SQL", "Insights", "Semantic", "Lineage"].map((tab) => (
            <button
              key={tab}
              className={`rounded-full px-3 py-1.5 text-xs ${
                tab === "Chart"
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
          <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-500">
            Line chart will render here
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Insights</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            <li>Revenue is up 14.2% YoY.</li>
            <li>West region drove the highest growth.</li>
            <li>South region shows stagnation risk.</li>
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Semantic Context</div>
          <div className="space-y-2 text-sm text-zinc-300">
            <div>
              <span className="text-zinc-500">Metric:</span> Revenue
            </div>
            <div>
              <span className="text-zinc-500">Dimensions:</span> Region, Month
            </div>
            <div>
              <span className="text-zinc-500">Engine:</span> StarRocks
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
