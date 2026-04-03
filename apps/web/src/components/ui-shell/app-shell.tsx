import { TopBar } from "@/components/layout/top-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { AnalysisPanel } from "@/components/analysis/analysis-panel";

export function AppShell() {
  return (
    <main className="h-screen bg-zinc-950 text-zinc-100">
      <div className="flex h-full flex-col">
        <TopBar />
        <div className="flex min-h-0 flex-1">
          <Sidebar />
          <ChatWorkspace />
          <AnalysisPanel />
        </div>
      </div>
    </main>
  );
}
