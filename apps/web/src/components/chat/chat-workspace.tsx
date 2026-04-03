import { ChatMessage } from "@/types/chat";
import { MessageCard } from "./message-card";
import { PromptInput } from "./prompt-input";

type ChatWorkspaceProps = {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  isLoading: boolean;
};

export function ChatWorkspace({
  messages,
  onSend,
  isLoading,
}: ChatWorkspaceProps) {
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

          {messages.map((message) => (
            <MessageCard key={message.id} {...message} />
          ))}

          {isLoading && (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-5">
              <div className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                DataPrismAI
              </div>
              <div className="text-sm text-zinc-400">Thinking...</div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-zinc-800 px-6 py-4">
        <div className="mx-auto max-w-4xl">
          <PromptInput onSend={onSend} isLoading={isLoading} />
        </div>
      </div>
    </section>
  );
}
