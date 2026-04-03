import { MessageCard } from "./message-card";
import { PromptInput } from "./prompt-input";

export function ChatWorkspace() {
  return (
    <section className="flex min-w-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold">DataPrismAI</h1>
            <p className="text-sm text-zinc-400">
              Ask questions about your business data, metrics, and trends.
            </p>
          </div>

          <MessageCard
            role="user"
            content="Show revenue trend by region for the last 12 months."
          />

          <MessageCard
            role="assistant"
            content={`Revenue increased 14.2% year over year over the last 12 months.

West region contributed the highest growth, while South remained nearly flat.

Key highlights:
- West: +22%
- East: +11%
- North: +9%
- South: +1%`}
            actions={["Show SQL", "Explain", "Change Chart", "Drill Down"]}
            followUps={[
              "Compare by segment",
              "Analyze South region",
              "Show monthly contribution",
            ]}
          />
        </div>
      </div>

      <div className="border-t border-zinc-800 px-6 py-4">
        <div className="mx-auto max-w-4xl">
          <PromptInput />
        </div>
      </div>
    </section>
  );
}
