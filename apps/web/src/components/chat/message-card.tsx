import { useState, useRef, useCallback, type ReactNode } from "react";
import { ChatMessage, ChartConfig } from "@/types/chat";
import { fetchSuggestions } from "@/lib/api";
import { InlineChartCard } from "./inline-chart-card";
import { MessageDetails } from "./message-details";

type MessageCardProps = ChatMessage & {
  onFollowUpClick?: (text: string) => void;
  userName?: string;
  persona?: string;
};

// ── Markdown → React renderer ─────────────────────────────────────────────────
function parseMarkdown(text: string): ReactNode {
  if (!text) return null;
  const lines = text.split("\n");
  const result: ReactNode[] = [];
  let i = 0;

  const inlineMd = (s: string) => (
    <span
      dangerouslySetInnerHTML={{
        __html: s
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.+?)\*/g, "<em>$1</em>")
          .replace(
            /`(.+?)`/g,
            '<code style="font-family:var(--font-mono);background:var(--tag-bg);padding:0 3px;border-radius:3px;font-size:0.85em">$1</code>',
          ),
      }}
    />
  );

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!trimmed) { i++; continue; }

    // Headings
    if (trimmed.startsWith("### ")) {
      result.push(<div key={i} className="mt-3 mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: "var(--accent-3)" }}>{trimmed.slice(4)}</div>);
      i++; continue;
    }
    if (trimmed.startsWith("## ")) {
      result.push(<div key={i} className="mt-3 mb-1 text-sm font-bold" style={{ color: "var(--accent-2)" }}>{trimmed.slice(3)}</div>);
      i++; continue;
    }
    if (trimmed.startsWith("# ")) {
      result.push(<div key={i} className="mt-3 mb-1 text-base font-bold" style={{ color: "var(--accent-1)" }}>{trimmed.slice(2)}</div>);
      i++; continue;
    }

    // HR
    if (trimmed === "---" || trimmed === "***") {
      result.push(<hr key={i} className="my-3" style={{ borderColor: "var(--card-border)" }} />);
      i++; continue;
    }

    // Table
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableRows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const row = lines[i].trim();
        if (/^\|[-\s|:]+\|$/.test(row)) { i++; continue; }
        tableRows.push(row.slice(1, -1).split("|").map((c) => c.trim()));
        i++;
      }
      if (tableRows.length > 0) {
        const headers = tableRows[0];
        const dataRows = tableRows.slice(1);
        result.push(
          <div key={`t-${i}`} className="my-3 overflow-x-auto rounded-lg" style={{ border: "1px solid var(--card-border)" }}>
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr style={{ backgroundColor: "var(--panel-bg)" }}>
                  {headers.map((h, ci) => (
                    <th key={ci} className="px-3 py-2 text-left font-semibold" style={{ color: "var(--muted)", borderBottom: "1px solid var(--card-border)" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataRows.map((row, ri) => (
                  <tr key={ri} style={{ borderBottom: ri < dataRows.length - 1 ? "1px solid var(--card-border)" : undefined }}>
                    {row.map((cell, ci) => (
                      <td key={ci} className="px-3 py-1.5" style={{ color: "var(--foreground)" }}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>,
        );
      }
      continue;
    }

    // Bullet list
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))) {
        items.push(lines[i].trim().slice(2));
        i++;
      }
      result.push(
        <ul key={`ul-${i}`} className="my-2 space-y-1.5 text-sm pl-1">
          {items.map((item, ji) => (
            <li key={ji} className="flex gap-2 items-start leading-relaxed">
              <span className="mt-2 shrink-0 h-1.5 w-1.5 rounded-full" style={{ backgroundColor: "var(--accent-1)" }} />
              <span>{inlineMd(item)}</span>
            </li>
          ))}
        </ul>,
      );
      continue;
    }

    // Numbered list
    if (/^\d+\.\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      result.push(
        <ol key={`ol-${i}`} className="my-2 space-y-1.5 text-sm">
          {items.map((item, ji) => (
            <li key={ji} className="flex gap-2 items-start leading-relaxed">
              <span className="shrink-0 font-bold text-xs mt-0.5" style={{ color: "var(--accent-2)", minWidth: "1.25rem" }}>{ji + 1}.</span>
              <span>{inlineMd(item)}</span>
            </li>
          ))}
        </ol>,
      );
      continue;
    }

    // Default paragraph
    result.push(
      <p key={i} className="text-sm leading-7 mb-1.5">{inlineMd(trimmed)}</p>,
    );
    i++;
  }

  return <>{result}</>;
}

// ── Collapsible section block (reasoning-style consistent) ───────────────────
function SectionBlock({
  open,
  onToggle,
  icon,
  title,
  count,
  subtitle,
  accentBorder,
  accentBg,
  accentText,
  children,
}: {
  open: boolean;
  onToggle: () => void;
  icon: string;
  title: string;
  count?: number;
  subtitle?: string;
  accentBorder: string;
  accentBg: string;
  accentText: string;
  children: ReactNode;
}) {
  return (
    <div className="mt-4 rounded-xl overflow-hidden" style={{ border: `1px solid ${accentBorder}` }}>
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-semibold"
        style={{ backgroundColor: accentBg, color: accentText }}
      >
        <span className="flex items-center gap-2 min-w-0">
          <span>{icon}</span>
          <span>{title}</span>
          {count !== undefined && count > 0 && (
            <span className="shrink-0 rounded-full px-1.5 py-0.5 text-[10px]" style={{ backgroundColor: "var(--tag-bg)", color: accentText }}>
              {count}
            </span>
          )}
          {!open && subtitle && (
            <span className="truncate ml-2 font-normal" style={{ color: "var(--muted)" }}>{subtitle}</span>
          )}
        </span>
        <span className="shrink-0 ml-2" style={{ color: "var(--muted)" }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="px-4 py-3 space-y-2" style={{ borderTop: `1px solid ${accentBorder}`, backgroundColor: "var(--step-bg)" }}>
          {children}
        </div>
      )}
    </div>
  );
}

export function MessageCard({
  role,
  content,
  responseMode = "metric",
  actions = [],
  followUps = [],
  insights = [],
  bottlenecks = [],
  highlightActions = [],
  kpiMetrics = [],
  insightRecommendations = [],
  assumptions = [],
  chartConfig,
  chartRecommendations = [],
  visualizationConfig,
  sql,
  sqlExplanation,
  sqlValidationIssues,
  resultColumns,
  resultRows,
  resultRowCount,
  resultEngine,
  resultExecutionTimeMs,
  reasoningSteps = [],
  sqlLlmUsed,
  answerLlmUsed,
  modelUsed,
  semanticContext,
  onFollowUpClick,
  userName,
  persona = "analyst",
}: MessageCardProps) {
  const isUser = role === "user";

  // Suppress analytics sections for raw table preview and schema responses
  const isDataPreview = responseMode === "table" || responseMode === "schema";

  const defaultChartConfig = chartConfig;
  const defaultChartId = "default";
  const initialChart = chartConfig ?? chartRecommendations?.[0]?.chart_config;

  const [activeChart, setActiveChart] = useState<ChartConfig | undefined>(initialChart);
  const [activeChartId, setActiveChartId] = useState(defaultChartId);
  const [cotOpen, setCotOpen] = useState(false);
  const [insightsOpen, setInsightsOpen] = useState(true);
  const [bottlenecksOpen, setBottlenecksOpen] = useState(true);
  const [actionsOpen, setActionsOpen] = useState(true);

  // ── Dynamic suggestions state ─────────────────────────────────────────────
  const metric = semanticContext?.metric || "";

  const [displayedRecs, setDisplayedRecs] = useState<string[]>(() => insightRecommendations.slice(0, 3));
  const [displayedFus,  setDisplayedFus]  = useState<string[]>(() => followUps.slice(0, 3));
  const [recRefreshing, setRecRefreshing] = useState(false);
  const [fuRefreshing,  setFuRefreshing]  = useState(false);
  // Accumulate all shown items so LLM knows what to avoid
  const shownRecsRef = useRef<string[]>(insightRecommendations.slice(0, 3));
  const shownFusRef  = useRef<string[]>(followUps.slice(0, 3));

  async function refreshRecs() {
    setRecRefreshing(true);
    try {
      const res = await fetchSuggestions(
        persona, metric, shownRecsRef.current, shownFusRef.current, content,
      );
      if (res.insight_recommendations.length > 0) {
        setDisplayedRecs(res.insight_recommendations);
        shownRecsRef.current = [...shownRecsRef.current, ...res.insight_recommendations];
      }
    } finally {
      setRecRefreshing(false);
    }
  }

  async function refreshFus() {
    setFuRefreshing(true);
    try {
      const res = await fetchSuggestions(
        persona, metric, shownRecsRef.current, shownFusRef.current, content,
      );
      if (res.follow_ups.length > 0) {
        setDisplayedFus(res.follow_ups);
        shownFusRef.current = [...shownFusRef.current, ...res.follow_ups];
      }
    } finally {
      setFuRefreshing(false);
    }
  }

  const cardRef = useRef<HTMLDivElement>(null);

  // ── Build a complete plain-text transcript of the response ──────────────
  function buildFullText(): string {
    const parts: string[] = [];
    const clean = (s: string) => s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/\*/g, "").trim();

    parts.push(clean(content));

    if (kpiMetrics.length > 0) {
      parts.push("\nKey Metrics:");
      kpiMetrics.forEach((k) => parts.push(`  ${k.label}: ${k.value}`));
    }
    if (insights.length > 0) {
      parts.push("\nKey Insights:");
      insights.forEach((s, i) => parts.push(`  ${i + 1}. ${clean(s)}`));
    }
    if (bottlenecks.length > 0) {
      parts.push("\nCritical Issues:");
      bottlenecks.forEach((s, i) => parts.push(`  ${i + 1}. ${clean(s)}`));
    }
    if (highlightActions.length > 0) {
      parts.push("\nRecommended Actions:");
      highlightActions.forEach((s, i) => parts.push(`  ${i + 1}. ${clean(s)}`));
    }
    if (insightRecommendations.length > 0) {
      parts.push("\nRecommended Analyses:");
      insightRecommendations.forEach((s) => parts.push(`  - ${s}`));
    }
    return parts.join("\n");
  }

  // ── Build a clean printable HTML from data props ──────────────────────────
  function buildPrintHTML(chartImgTag: string = ""): string {
    const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const mdToHtml = (s: string) =>
      esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>");

    let body = `<h1 style="color:#00A551;font-size:18pt;margin-top:0">DataPrismAI Response</h1>
<p style="color:#888;font-size:9pt;margin-bottom:20px">Generated ${new Date().toLocaleString()}</p>
<div style="font-size:11pt;line-height:1.7">${mdToHtml(content)}</div>\n`;

    // Embed chart SVG right after the main content if available
    if (chartImgTag) {
      body += chartImgTag + "\n";
    }

    if (kpiMetrics.length > 0) {
      body += `<h2 style="color:#1A6FE0;margin-top:24px;font-size:12pt">Key Metrics</h2>
<table style="border-collapse:collapse;width:100%;margin-bottom:16px">
<thead><tr>${kpiMetrics.map(k => `<th style="border:1px solid #ccc;padding:6px 10px;background:#f0f0f0;font-size:9pt;text-transform:uppercase">${esc(k.label)}</th>`).join("")}</tr></thead>
<tbody><tr>${kpiMetrics.map(k => `<td style="border:1px solid #ccc;padding:8px 10px;font-size:14pt;font-weight:bold;color:${k.trend==="up"?"#00A551":k.trend==="down"?"#ef4444":"#111"}">${esc(k.value)}</td>`).join("")}</tr></tbody>
</table>\n`;
    }

    if (insights.length > 0) {
      body += `<h2 style="color:#1A6FE0;margin-top:24px;font-size:12pt">📈 Key Insights</h2><ol style="margin:0 0 16px;padding-left:20px">`;
      insights.forEach(s => { body += `<li style="margin-bottom:6px;font-size:10.5pt">${mdToHtml(s)}</li>`; });
      body += `</ol>\n`;
    }

    if (bottlenecks.length > 0) {
      body += `<h2 style="color:#ef4444;margin-top:24px;font-size:12pt">⚠ Critical Issues</h2><ol style="margin:0 0 16px;padding-left:20px">`;
      bottlenecks.forEach(s => { body += `<li style="margin-bottom:6px;font-size:10.5pt">${mdToHtml(s)}</li>`; });
      body += `</ol>\n`;
    }

    if (highlightActions.length > 0) {
      body += `<h2 style="color:#00A551;margin-top:24px;font-size:12pt">💡 Recommended Actions</h2><ol style="margin:0 0 16px;padding-left:20px">`;
      highlightActions.forEach(s => { body += `<li style="margin-bottom:6px;font-size:10.5pt">${mdToHtml(s)}</li>`; });
      body += `</ol>\n`;
    }

    if (resultColumns && resultRows && resultRows.length > 0) {
      body += `<h2 style="color:#1A6FE0;margin-top:24px;font-size:12pt">Query Results (${resultRowCount ?? resultRows.length} rows)</h2>
<table style="border-collapse:collapse;width:100%;font-size:9pt;margin-bottom:16px">
<thead><tr>${resultColumns.map(c => `<th style="border:1px solid #ccc;padding:5px 8px;background:#f0f0f0;text-align:left">${esc(c)}</th>`).join("")}</tr></thead>
<tbody>${resultRows.slice(0, 200).map((row, i) =>
  `<tr style="background:${i%2===0?"#fff":"#f9f9f9"}">${resultColumns!.map(c => `<td style="border:1px solid #e0e0e0;padding:4px 8px">${esc(String(row[c] ?? ""))}</td>`).join("")}</tr>`
).join("")}</tbody></table>\n`;
    }

    if (sql) {
      body += `<h2 style="color:#1A6FE0;margin-top:24px;font-size:12pt">SQL Query</h2>
<pre style="background:#f5f5f5;padding:12px;border-radius:4px;font-size:9pt;font-family:monospace;white-space:pre-wrap;border:1px solid #ddd">${esc(sql)}</pre>\n`;
    }

    return body;
  }

  const downloadPDF = useCallback(() => {
    // Capture ECharts canvas from this card's DOM before building the HTML
    let chartImgTag = "";
    if (cardRef.current) {
      const canvasEl = cardRef.current.querySelector<HTMLCanvasElement>("canvas");
      if (canvasEl) {
        try {
          const dataUrl = canvasEl.toDataURL("image/png");
          chartImgTag = `<h2 style="color:#1A6FE0;margin-top:24px;font-size:12pt">Chart</h2>
<img src="${dataUrl}" style="max-width:100%;height:auto;margin-bottom:16px;border:1px solid #e0e0e0;border-radius:6px" />`;
        } catch {
          // ignore — chart simply won't appear in PDF (e.g. cross-origin tainted canvas)
        }
      }
    }

    const body = buildPrintHTML(chartImgTag);
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><title>DataPrismAI Response</title>
<style>*{box-sizing:border-box}body{font-family:Calibri,Arial,sans-serif;padding:32px;max-width:900px;margin:auto;color:#111}
@page{margin:2cm}@media print{body{padding:0}}</style></head><body>${body}</body></html>`);
    win.document.close();
    setTimeout(() => { win.print(); win.close(); }, 500);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content, kpiMetrics, insights, bottlenecks, highlightActions, resultColumns, resultRows, resultRowCount, sql]);

  const lastFollowUpRef = useRef<{ text: string; time: number }>({ text: "", time: 0 });
  function safeFollowUp(text: string) {
    const now = Date.now();
    if (text === lastFollowUpRef.current.text && now - lastFollowUpRef.current.time < 800) return;
    lastFollowUpRef.current = { text, time: now };
    onFollowUpClick?.(text);
  }

  const enrichedMessage: ChatMessage = {
    id: "details",
    role,
    content,
    actions,
    followUps,
    insights,
    insightRecommendations,
    assumptions,
    chartConfig: activeChart,
    chartRecommendations,
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

  /* ── User message — right-aligned text bubble ─────────────────── */
  if (isUser) {
    const displayName = userName ?? "You";
    return (
      <div className="flex justify-end items-end gap-2">
        <div className="max-w-[72%]">
          <div
            className="rounded-3xl rounded-br-md px-4 py-3 shadow-lg"
            style={{
              background: "linear-gradient(135deg, #1A6FE0 0%, #1458B8 100%)",
              color: "#ffffff",
            }}
          >
            <div className="whitespace-pre-line text-sm leading-6">{content}</div>
          </div>
          {onFollowUpClick && (
            <div className="mt-1 flex justify-end">
              <button
                onClick={() => safeFollowUp(content)}
                title="Resubmit this question"
                className="flex items-center gap-1 text-[10px] rounded-full px-2 py-0.5 opacity-40 hover:opacity-100 transition-opacity"
                style={{ color: "var(--muted)", backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}
              >
                ↺ Resubmit
              </button>
            </div>
          )}
        </div>
        {/* Avatar */}
        <div
          className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold shadow"
          style={{ background: "linear-gradient(135deg, #1A6FE0 0%, #1458B8 100%)", color: "#fff" }}
          title={displayName}
        >
          {displayName.charAt(0).toUpperCase()}
        </div>
      </div>
    );
  }

  const cotSummary = reasoningSteps.length > 0
    ? reasoningSteps.map((s) => {
        if (s.startsWith("Guardrail")) return "Guardrail ✓";
        if (s.startsWith("Semantic")) return s.includes("free-form") ? "Free-form SQL" : "Metric matched";
        if (s.startsWith("SQL generation")) return "SQL generated";
        if (s.startsWith("Query execution")) return s.replace("Query execution: ", "");
        if (s.startsWith("Insight")) return "Insights ready";
        return s.split(":")[0];
      }).join(" → ")
    : "";

  // TTS playback — reads all sections, chunked to avoid browser utterance limits
  const [isSpeaking, setIsSpeaking] = useState(false);
  const ttsChunksRef = useRef<string[]>([]);
  const ttsChunkIdxRef = useRef(0);

  function speakNextChunk() {
    const idx = ttsChunkIdxRef.current;
    const chunks = ttsChunksRef.current;
    if (idx >= chunks.length) { setIsSpeaking(false); return; }
    const utt = new SpeechSynthesisUtterance(chunks[idx]);
    utt.lang = "en-US";
    utt.rate = 1.0;
    utt.onend = () => {
      ttsChunkIdxRef.current += 1;
      speakNextChunk();
    };
    utt.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utt);
  }

  function toggleTTS() {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      ttsChunksRef.current = [];
      ttsChunkIdxRef.current = 0;
      setIsSpeaking(false);
      return;
    }
    // Build full text from ALL sections
    const fullText = buildFullText();
    // Split into ~200 word chunks to avoid browser utterance limits
    const words = fullText.split(/\s+/);
    const CHUNK = 200;
    const chunks: string[] = [];
    for (let i = 0; i < words.length; i += CHUNK) {
      chunks.push(words.slice(i, i + CHUNK).join(" "));
    }
    ttsChunksRef.current = chunks;
    ttsChunkIdxRef.current = 0;
    setIsSpeaking(true);
    window.speechSynthesis.cancel();
    speakNextChunk();
  }

  /* ── AI message ───────────────────────────────────────────────── */
  return (
    <div className="flex justify-start items-start gap-2">
      {/* AI Avatar */}
      <div
        className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold shadow mt-1"
        style={{ background: "linear-gradient(135deg, #00A551 0%, #007A3D 100%)", color: "#fff" }}
        title="DataPrismAI"
      >
        ✦
      </div>
    <div
      ref={cardRef}
      className="w-full rounded-2xl rounded-tl-md p-5 shadow-md"
      style={{
        maxWidth: "88%",
        background: "var(--ai-bubble-bg)",
        border: "1px solid var(--ai-bubble-border)",
        borderLeft: "3px solid var(--ai-bubble-border-left)",
      }}
    >
      {/* Header */}
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--ai-label-color)", fontFamily: "var(--font-display)" }}>
          DataPrismAI
        </span>
        {/* Response mode badge for table/schema previews */}
        {responseMode === "table" && (
          <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
            style={{ backgroundColor: "rgba(0,165,81,0.12)", color: "var(--accent-1)", border: "1px solid rgba(0,165,81,0.3)" }}>
            Data Preview
          </span>
        )}
        {responseMode === "schema" && (
          <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
            style={{ backgroundColor: "rgba(26,111,224,0.12)", color: "var(--accent-2)", border: "1px solid rgba(26,111,224,0.3)" }}>
            Schema
          </span>
        )}
        {/* Spacer */}
        <div className="flex-1" />
        {/* Download buttons */}
        <button
          onClick={downloadPDF}
          title="Download / Print as PDF"
          className="rounded-lg px-2 py-1 text-[10px] font-medium transition-opacity hover:opacity-80 no-print"
          style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--tag-bg)", color: "var(--muted)" }}
        >
          ⬇ PDF
        </button>
        <button
          onClick={toggleTTS}
          title={isSpeaking ? "Stop reading" : "Read aloud"}
          className="rounded-lg px-2 py-1 text-[10px] font-medium transition-opacity hover:opacity-80 no-print"
          style={{
            border: `1px solid ${isSpeaking ? "var(--accent-2)" : "var(--card-border)"}`,
            backgroundColor: isSpeaking ? "rgba(26,111,224,0.1)" : "var(--tag-bg)",
            color: isSpeaking ? "var(--accent-2)" : "var(--muted)",
          }}
        >
          {isSpeaking ? "⏹ Stop" : "🔊"}
        </button>
      </div>

      {/* Main answer — rich markdown rendering */}
      <div style={{ color: "var(--foreground)" }}>
        {parseMarkdown(content)}
      </div>

      {/* ── Model / generation path badge — always visible ─────── */}
      {!isUser && modelUsed && (
        <div className="mt-2 flex items-center gap-1.5 no-print">
          {(answerLlmUsed || sqlLlmUsed) ? (
            <>
              <span className="text-[10px]" style={{ color: "var(--muted)" }}>
                {sqlLlmUsed && answerLlmUsed ? "SQL + Answer by" : answerLlmUsed ? "Answer by" : "SQL by"}
              </span>
              <span
                className="rounded px-2 py-0.5 text-[10px] font-mono font-semibold"
                style={{ backgroundColor: "rgba(26,111,224,0.1)", color: "var(--accent-2)", border: "1px solid rgba(26,111,224,0.25)" }}
              >
                🤖 {modelUsed}
              </span>
            </>
          ) : (
            <>
              <span className="text-[10px]" style={{ color: "var(--muted)" }}>SQL via</span>
              <span
                className="rounded px-2 py-0.5 text-[10px] font-mono font-semibold"
                style={{ backgroundColor: "rgba(0,165,81,0.08)", color: "var(--accent-1)", border: "1px solid rgba(0,165,81,0.25)" }}
              >
                ⚡ Pattern matched
              </span>
              <span className="text-[10px]" style={{ color: "var(--muted)" }}>· model</span>
              <span
                className="rounded px-2 py-0.5 text-[10px] font-mono"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--muted)", border: "1px solid var(--card-border)" }}
              >
                {modelUsed}
              </span>
            </>
          )}
        </div>
      )}

      {/* ── KPI Metric Cards (metric/insight mode only) ────────── */}
      {!isDataPreview && kpiMetrics.length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {kpiMetrics.map((kpi) => (
            <div
              key={kpi.label}
              className="rounded-xl p-3"
              style={{ backgroundColor: "var(--panel-bg)", border: "1px solid var(--card-border)" }}
            >
              <div className="text-[10px] font-semibold uppercase tracking-wide mb-1" style={{ color: "var(--muted)" }}>
                {kpi.label}
              </div>
              <div
                className="text-xl font-bold"
                style={{ color: kpi.trend === "up" ? "var(--accent-1)" : kpi.trend === "down" ? "#ef4444" : "var(--foreground)", fontFamily: "var(--font-display)" }}
              >
                {kpi.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Key Insights (metric/insight mode only) ─────────────── */}
      {!isDataPreview && insights.length > 0 && (
        <SectionBlock
          open={insightsOpen}
          onToggle={() => setInsightsOpen((v) => !v)}
          icon="📈"
          title="Key Insights"
          count={insights.length}
          accentBorder="rgba(0,212,255,0.3)"
          accentBg="rgba(0,212,255,0.06)"
          accentText="var(--accent-3)"
        >
          <div className="space-y-2">
            {insights.map((item, i) => {
              // Split at " — " or ". " after first sentence for a title+detail layout
              const boldMatch = item.match(/^\*\*(.+?)\*\*/);
              const title = boldMatch ? boldMatch[1] : `Finding ${i + 1}`;
              const body = boldMatch ? item.slice(boldMatch[0].length).replace(/^[\s—:]+/, "") : item;
              return (
                <div
                  key={i}
                  className="rounded-lg px-3 py-2.5"
                  style={{
                    backgroundColor: "var(--panel-bg)",
                    borderLeft: "3px solid rgba(0,212,255,0.5)",
                    border: "1px solid rgba(0,212,255,0.18)",
                    borderLeftWidth: "3px",
                  }}
                >
                  <div className="flex items-start gap-2">
                    <span
                      className="mt-0.5 shrink-0 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
                      style={{ backgroundColor: "rgba(0,212,255,0.15)", color: "var(--accent-3)" }}
                    >
                      {i + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold mb-0.5" style={{ color: "var(--accent-3)" }}>
                        {title}
                      </div>
                      <div
                        className="text-xs leading-relaxed"
                        style={{ color: "var(--foreground)", opacity: 0.9 }}
                        dangerouslySetInnerHTML={{ __html: body.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </SectionBlock>
      )}

      {/* ── Bottlenecks / Critical Issues (metric/insight mode only) ── */}
      {!isDataPreview && bottlenecks.length > 0 && (
        <SectionBlock
          open={bottlenecksOpen}
          onToggle={() => setBottlenecksOpen((v) => !v)}
          icon="⚠"
          title="Critical Issues"
          count={bottlenecks.length}
          accentBorder="rgba(239,68,68,0.35)"
          accentBg="rgba(239,68,68,0.08)"
          accentText="#ef4444"
        >
          <div className="space-y-2">
            {bottlenecks.map((item, i) => {
              const boldMatch = item.match(/^\*\*(.+?)\*\*/);
              const title = boldMatch ? boldMatch[1] : `Issue ${i + 1}`;
              const body = boldMatch ? item.slice(boldMatch[0].length).replace(/^[\s—:]+/, "") : item;
              return (
                <div
                  key={i}
                  className="rounded-lg px-3 py-2.5"
                  style={{
                    backgroundColor: "rgba(239,68,68,0.05)",
                    border: "1px solid rgba(239,68,68,0.2)",
                    borderLeftWidth: "3px",
                    borderLeftColor: "#ef4444",
                  }}
                >
                  <div className="flex items-start gap-2">
                    <span className="mt-0.5 text-sm shrink-0">⚠</span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold mb-0.5" style={{ color: "#ef4444" }}>
                        {title}
                      </div>
                      <div
                        className="text-xs leading-relaxed"
                        style={{ color: "var(--foreground)", opacity: 0.9 }}
                        dangerouslySetInnerHTML={{ __html: body.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </SectionBlock>
      )}

      {/* ── Recommended Actions (metric/insight mode only) ────────── */}
      {!isDataPreview && highlightActions.length > 0 && (
        <SectionBlock
          open={actionsOpen}
          onToggle={() => setActionsOpen((v) => !v)}
          icon="💡"
          title="Recommended Actions"
          count={highlightActions.length}
          accentBorder="rgba(0,165,81,0.35)"
          accentBg="rgba(0,165,81,0.08)"
          accentText="var(--accent-1)"
        >
          <div className="space-y-2">
            {highlightActions.map((item, i) => {
              // "**Title:** explanation text"
              const boldMatch = item.match(/^\*\*(.+?)\*\*:?\s*/);
              const title = boldMatch ? boldMatch[1] : `Action ${i + 1}`;
              const body = boldMatch ? item.slice(boldMatch[0].length) : item;
              return (
                <div
                  key={i}
                  className="rounded-lg px-3 py-2.5"
                  style={{
                    backgroundColor: "rgba(0,165,81,0.06)",
                    border: "1px solid rgba(0,165,81,0.2)",
                    borderLeftWidth: "3px",
                    borderLeftColor: "var(--accent-1)",
                  }}
                >
                  <div className="flex items-start gap-2">
                    <span
                      className="mt-0.5 shrink-0 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
                      style={{ backgroundColor: "rgba(0,165,81,0.15)", color: "var(--accent-1)" }}
                    >
                      {i + 1}
                    </span>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold mb-0.5" style={{ color: "var(--accent-1)" }}>
                        {title}
                      </div>
                      <div
                        className="text-xs leading-relaxed"
                        style={{ color: "var(--foreground)", opacity: 0.9 }}
                        dangerouslySetInnerHTML={{ __html: body.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>") }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </SectionBlock>
      )}

      {/* ── Chart recommendations (metric/insight mode only) ────── */}
      {!isDataPreview && chartRecommendations.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-xs font-semibold" style={{ color: "var(--accent-3)" }}>
              Visualizations
              <span className="ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-3)" }}>
                {chartRecommendations.length}
              </span>
            </h3>
            {activeChartId !== defaultChartId && (
              <button
                onClick={() => { setActiveChart(defaultChartConfig); setActiveChartId(defaultChartId); }}
                className="rounded-full px-2 py-1 text-[10px] font-medium"
                style={{ border: "1px solid var(--accent-1)", color: "var(--accent-1)", backgroundColor: "var(--tag-bg)" }}
              >
                Restore Default
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {chartRecommendations.map((rec) => {
              const isActive = activeChartId === rec.id;
              return (
                <button
                  key={rec.id}
                  onClick={() => { setActiveChart(rec.chart_config); setActiveChartId(rec.id); }}
                  className="rounded-full px-3 py-1.5 text-xs transition-all duration-150"
                  style={isActive
                    ? { backgroundColor: "var(--accent-1)", color: "white", border: "1px solid var(--accent-1)" }
                    : { border: "1px solid var(--card-border)", color: "var(--foreground)", backgroundColor: "var(--panel-bg)" }
                  }
                  title={rec.reason}
                >
                  {rec.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Chart (metric/insight mode only) ───────────────── */}
      {!isDataPreview && (activeChart || visualizationConfig) && (
        <InlineChartCard chartConfig={activeChart} visualizationConfig={visualizationConfig} />
      )}

      {/* ── SQL / Semantic Context / Result Preview ───────────────── */}
      <MessageDetails message={enrichedMessage} />

      {/* ── Chain of Thought — collapsible, last ─────────────────── */}
      {reasoningSteps.length > 0 && (
        <SectionBlock
          open={cotOpen}
          onToggle={() => setCotOpen((v) => !v)}
          icon="🧠"
          title="Reasoning"
          count={reasoningSteps.length}
          subtitle={cotSummary}
          accentBorder="var(--card-border)"
          accentBg="var(--step-bg)"
          accentText="var(--foreground)"
        >
          {modelUsed && (
            <div className="mb-2 flex items-center gap-1.5">
              <span className="text-[10px]" style={{ color: "var(--muted)" }}>Model:</span>
              <span
                className="rounded px-2 py-0.5 text-[10px] font-mono font-medium"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-2)" }}
              >
                {modelUsed}
              </span>
              {!sqlLlmUsed && !answerLlmUsed && (
                <span className="text-[10px]" style={{ color: "var(--muted)" }}>
                  · SQL was pattern-matched, not LLM-generated
                </span>
              )}
              {!sqlLlmUsed && answerLlmUsed && (
                <span className="text-[10px]" style={{ color: "var(--muted)" }}>
                  · SQL pattern-matched · answer narrated by LLM
                </span>
              )}
            </div>
          )}
          {reasoningSteps.map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <span
                className="mt-px shrink-0 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--step-num)" }}
              >
                {i + 1}
              </span>
              <span className="text-xs leading-relaxed" style={{ color: "var(--foreground)" }}>{step}</span>
            </div>
          ))}
        </SectionBlock>
      )}

      {/* ── Recommended Analyses — always expanded, very last ────── */}
      {(insightRecommendations.length > 0 || displayedRecs.length > 0) && (
        <div className="mt-4 rounded-xl overflow-hidden" style={{ border: "1px solid rgba(26,111,224,0.35)" }}>
          <div
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold"
            style={{ backgroundColor: "rgba(26,111,224,0.08)", color: "var(--accent-2)" }}
          >
            <span>🔬</span>
            <span>Recommended Analyses</span>
            {insightRecommendations.length > 0 && (
              <button
                onClick={refreshRecs}
                disabled={recRefreshing}
                title="Load new AI-generated recommendations"
                className="ml-auto flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-all hover:opacity-80 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-2)", border: "1px solid var(--card-border)" }}
              >
                <span className={recRefreshing ? "inline-block animate-spin" : "inline-block"}>↻</span>
                {recRefreshing ? "Loading…" : "Refresh"}
              </button>
            )}
          </div>
          <div
            className="px-4 py-3 flex flex-wrap gap-2"
            style={{ borderTop: "1px solid rgba(26,111,224,0.2)", backgroundColor: "var(--step-bg)" }}
          >
            {displayedRecs.map((item) => (
              <button
                key={item}
                onClick={() => safeFollowUp(item)}
                className="rounded-full px-3 py-1.5 text-xs transition-colors hover:opacity-80"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--foreground)", border: "1px solid var(--card-border)" }}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Suggested Follow-ups (metric/insight mode only) ──────── */}
      {!isDataPreview && (followUps.length > 0 || displayedFus.length > 0) && (
        <div className="mt-4 rounded-xl overflow-hidden" style={{ border: "1px solid rgba(26,111,224,0.35)" }}>
          <div
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold"
            style={{ backgroundColor: "rgba(26,111,224,0.08)", color: "var(--accent-2)" }}
          >
            <span>💬</span>
            <span>Suggested Follow-ups</span>
            {followUps.length > 0 && (
              <button
                onClick={refreshFus}
                disabled={fuRefreshing}
                title="Load new AI-generated follow-up questions"
                className="ml-auto flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-all hover:opacity-80 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-2)", border: "1px solid var(--card-border)" }}
              >
                <span className={fuRefreshing ? "inline-block animate-spin" : "inline-block"}>↻</span>
                {fuRefreshing ? "Loading…" : "Refresh"}
              </button>
            )}
          </div>
          <div
            className="px-4 py-3 flex flex-wrap gap-2"
            style={{ borderTop: "1px solid rgba(26,111,224,0.2)", backgroundColor: "var(--step-bg)" }}
          >
            {displayedFus.map((item) => (
              <button
                key={item}
                onClick={() => safeFollowUp(item)}
                className="rounded-full px-3 py-1.5 text-xs transition-colors hover:opacity-80"
                style={{ backgroundColor: "var(--tag-bg)", color: "var(--accent-2)", border: "1px solid var(--card-border)" }}
              >
                → {item}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
    </div>
  );
}
