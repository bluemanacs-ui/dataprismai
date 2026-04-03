import { AnalysisState } from "@/types/chat";
import { AnalysisTabs } from "./analysis-tabs";

type AnalysisPanelProps = {
  analysis: AnalysisState;
};

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  return (
    <aside className="hidden w-[380px] border-l border-zinc-800 bg-zinc-950 xl:flex xl:flex-col">
      <AnalysisTabs analysis={analysis} />
    </aside>
  );
}
