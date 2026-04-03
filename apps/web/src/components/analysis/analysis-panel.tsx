import { AnalysisTabs } from "./analysis-tabs";

export function AnalysisPanel() {
  return (
    <aside className="hidden w-[380px] border-l border-zinc-800 bg-zinc-950 xl:flex xl:flex-col">
      <AnalysisTabs />
    </aside>
  );
}
