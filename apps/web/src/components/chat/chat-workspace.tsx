"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/types/chat";
import { MessageCard } from "./message-card";
import { PromptInput } from "./prompt-input";

const TIME_RANGE_OPTIONS = [
  { label: "All", value: "ALL" },
  { label: "L7D", value: "L7D" },
  { label: "L1M", value: "L1M" },
  { label: "LQ",  value: "LQ" },
  { label: "L1Y", value: "L1Y" },
];

type ChatWorkspaceProps = {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  isLoading: boolean;
  persona?: string;
  userName?: string;
  timeRange?: string;
  onTimeRangeChange?: (t: string) => void;
};

export function ChatWorkspace({
  messages,
  onSend,
  isLoading,
  persona = "analyst",
  userName,
  timeRange = "ALL",
  onTimeRangeChange,
}: ChatWorkspaceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
      {/* ── Time-range filter pills ────────────────────────────────────── */}
      {onTimeRangeChange && (
        <div
          className="flex items-center gap-2 border-b px-4 py-2"
          style={{ borderColor: "var(--card-border)", backgroundColor: "var(--sidebar-bg, var(--background))" }}
        >
          <span className="text-[11px] font-medium uppercase tracking-wider" style={{ color: "var(--muted)" }}>
            Time range:
          </span>
          <div className="flex gap-1">
            {TIME_RANGE_OPTIONS.map((opt) => {
              const active = (timeRange || "ALL") === opt.value;
              return (
                <button
                  key={opt.value}
                  onClick={() => onTimeRangeChange(opt.value)}
                  className="rounded px-2.5 py-0.5 text-[11px] font-semibold transition-colors"
                  style={{
                    backgroundColor: active ? "var(--accent-1)" : "var(--card-bg)",
                    color: active ? "white" : "var(--muted)",
                    border: `1px solid ${active ? "var(--accent-1)" : "var(--card-border)"}`,
                    cursor: "pointer",
                  }}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Messages ──────────────────────────────────────────────────── */}
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

          {isLoading && (
            <div className="flex justify-start items-start gap-2">
              {/* AI Avatar */}
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

      {/* ── Input + footer ─────────────────────────────────────────────── */}
      <div className="border-t px-4 pt-3 pb-2" style={{ borderColor: "var(--card-border)" }}>
        <div className="mx-auto" style={{ maxWidth: "80%" }}>
          <PromptInput
            onSend={onSend}
            isLoading={isLoading}
            userName={userName}
          />
          <div className="mt-2 text-center text-[10px]" style={{ color: "var(--muted)" }}>
            Powered by DataPrismAI · StarRocks · qwen2.5&nbsp;&nbsp;|&nbsp;&nbsp;© {new Date().getFullYear()} DataPrismAI
          </div>
        </div>
      </div>
    </section>
  );
}
