import { ChatMessage } from "@/types/chat";
import { InlineChartCard } from "./inline-chart-card";
import { MessageDetails } from "./message-details";

type MessageCardProps = ChatMessage;

export function MessageCard({
  role,
  content,
  actions = [],
  followUps = [],
  insights = [],
  assumptions = [],
  chartConfig,
  sql,
  sqlExplanation,
  sqlValidationIssues,
  resultColumns,
  resultRows,
  resultRowCount,
  resultEngine,
  resultExecutionTimeMs,
  semanticContext,
}: MessageCardProps) {
  const isUser = role === "user";

  const enrichedMessage: ChatMessage = {
    id: "details",
    role,
    content,
    actions,
    followUps,
    insights,
    assumptions,
    chartConfig,
    sql,
    sqlExplanation,
    sqlValidationIssues,
    resultColumns,
    resultRows,
    resultRowCount,
    resultEngine,
    resultExecutionTimeMs,
    semanticContext,
  };

  return (
    <div
      className={`rounded-2xl border p-5 shadow-sm ${isUser
          ? "border-zinc-800 bg-zinc-900"
          : "border-zinc-800 bg-zinc-950"
        }`}
    >
      <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
        {isUser ? "You" : "DataPrismAI"}
      </div>

      <div className="whitespace-pre-line text-sm leading-7 text-zinc-100">
        {content}
      </div>

      {!isUser && chartConfig ? <InlineChartCard chartConfig={chartConfig} /> : null}

      {!isUser && insights.length > 0 ? (
        <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
          <div className="mb-2 text-sm font-semibold">Key Insights</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {insights.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {!isUser && actions.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action}
              className="rounded-full border border-zinc-700 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-900"
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {!isUser && followUps.length > 0 && (
        <div className="mt-5">
          <div className="mb-2 text-xs font-medium text-zinc-500">
            Suggested follow-ups
          </div>
          <div className="flex flex-wrap gap-2">
            {followUps.map((item) => (
              <button
                key={item}
                className="rounded-full bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}

      {!isUser ? <MessageDetails message={enrichedMessage} /> : null}
    </div>
  );
}
