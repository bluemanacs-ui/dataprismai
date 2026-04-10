"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/types/chat";
import { MessageCard } from "./message-card";
import { PromptInput } from "./prompt-input";

type ChatWorkspaceProps = {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  isLoading: boolean;
  persona?: string;
  userName?: string;
  chatMode?: string;
  onChatModeChange?: (m: string) => void;
};

export function ChatWorkspace({
  messages,
  onSend,
  isLoading,
  persona = "analyst",
  userName,
  chatMode = "hybrid",
  onChatModeChange,
}: ChatWorkspaceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5">
        <div className="mx-auto w-full space-y-5" style={{ maxWidth: "80%" }}>
          {messages.map((message) => (
            <MessageCard
              key={message.id}
              {...message}
              onFollowUpClick={onSend}
              userName={userName}
              persona={persona}
            />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start items-start gap-2">
              <div
                className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold shadow mt-1"
                style={{ background: "linear-gradient(135deg, #00A551 0%, #007A3D 100%)", color: "#fff" }}
              >
                ✦
              </div>
              <div
                className="rounded-2xl rounded-tl-md p-5 shadow-md"
                style={{
                  maxWidth: "88%",
                  background: "var(--ai-bubble-bg)",
                  border: "1px solid var(--ai-bubble-border)",
                  borderLeft: "3px solid var(--ai-bubble-border-left)",
                }}
              >
                <div className="mb-3 flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--ai-label-color)" }}>
                    DataPrismAI
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm" style={{ color: "var(--muted)" }}>
                  <span>Thinking</span>
                  <span className="flex items-end gap-1">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input + footer */}
      <div className="border-t px-4 pt-3 pb-2" style={{ borderColor: "var(--card-border)" }}>
        <div className="mx-auto" style={{ maxWidth: "80%" }}>
          <PromptInput onSend={onSend} isLoading={isLoading} userName={userName} />
          <div className="mt-2 text-center text-[10px]" style={{ color: "var(--muted)" }}>
            Powered by DataPrismAI · StarRocks · qwen2.5&nbsp;&nbsp;|&nbsp;&nbsp;© {new Date().getFullYear()} DataPrismAI
          </div>
        </div>
      </div>
    </section>
  );
}
