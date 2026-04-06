"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type PromptInputProps = {
  onSend: (message: string) => void;
  isLoading?: boolean;
  userName?: string;
};

export function PromptInput({
  onSend,
  isLoading = false,
  userName,
}: PromptInputProps) {
  const [value, setValue] = useState("");
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<{ stop: () => void } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea — hide scrollbar until content overflows max height
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const clamped = Math.min(el.scrollHeight, 140);
    el.style.height = clamped + "px";
    el.style.overflowY = el.scrollHeight > 140 ? "auto" : "hidden";
  }, [value]);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  }, [value, isLoading, onSend]);

  // ── Voice input ───────────────────────────────────────────────────────────
  function toggleListening() {
    if (typeof window === "undefined") return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const anyWin = window as any;
    const SR = anyWin.SpeechRecognition ?? anyWin.webkitSpeechRecognition;
    if (!SR) {
      alert("Voice input is not supported in this browser.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const r = new SR();
    r.continuous = false;
    r.interimResults = false;
    r.lang = "en-US";
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    r.onresult = (e: any) => {
      const text = e.results[0]?.[0]?.transcript ?? "";
      if (text) setValue((prev: string) => (prev ? prev + " " + text : text));
    };
    r.onerror = () => setListening(false);
    r.onend = () => setListening(false);
    recognitionRef.current = r;
    r.start();
    setListening(true);
  }

  const canSend = !isLoading && value.trim().length > 0;

  return (
    <div className="space-y-2">
      {/* ── Main input row ─────────────────────────────────────────────── */}
      <div
        className="flex items-end gap-2 rounded-2xl px-3 py-2.5"
        style={{
          background: "linear-gradient(135deg, rgba(26,111,224,0.08) 0%, rgba(20,88,184,0.06) 100%)",
          borderTop: "1px solid rgba(26,111,224,0.3)",
          borderBottom: "1px solid rgba(26,111,224,0.3)",
          borderLeft: "3px solid #1A6FE0",
          borderRight: "3px solid #1A6FE0",
        }}
      >
        {/* Voice button */}
        <button
          type="button"
          onClick={toggleListening}
          title={listening ? "Stop listening" : "Voice input"}
          className="mb-1 shrink-0 rounded-xl p-1.5 transition-all"
          style={{
            backgroundColor: listening ? "rgba(239,68,68,0.15)" : "rgba(26,111,224,0.15)",
            color: listening ? "#ef4444" : "#60a5fa",
            border: `1px solid ${listening ? "rgba(239,68,68,0.4)" : "rgba(26,111,224,0.4)"}`,
          }}
        >
          {listening ? (
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
            </svg>
          ) : (
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
          )}
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder={listening ? "Listening… speak now" : "Ask me and get instant data insights!"}
          className="flex-1 resize-none bg-transparent px-1 py-1.5 text-sm outline-none leading-snug"
          style={{ color: "var(--foreground)", minHeight: 28, maxHeight: 140, overflowY: "hidden" }}
        />

        {/* Send button — blue bubble */}
        <button
          onClick={handleSubmit}
          disabled={!canSend}
          className="mb-0.5 shrink-0 rounded-xl p-2.5 text-sm font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40"
          style={{
            backgroundColor: canSend ? "var(--accent-2)" : "var(--tag-bg)",
            color: "white",
          }}
          title="Send (Enter)"
        >
          {isLoading ? (
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24" className="animate-spin">
              <circle cx="12" cy="12" r="9" strokeDasharray="56" strokeDashoffset="14" opacity="0.6"/>
            </svg>
          ) : (
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          )}
        </button>
      </div>

    </div>
  );
}
