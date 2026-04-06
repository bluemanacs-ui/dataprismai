"use client";

import { useEffect, useRef, useState } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { ExplorerPanel } from "@/components/explorer/explorer-panel";
import { ReportsPanel } from "@/components/chat/reports-panel";
import { AuditPanel } from "@/components/audit/audit-panel";
import { SettingsPanel } from "@/components/settings/settings-panel";
import { LoginPanel } from "@/components/auth/login-panel";
import { HelpPanel } from "@/components/help/help-panel";
import {
  ChatMessage,
  SemanticCatalogResponse,
} from "@/types/chat";
import { fetchSemanticCatalog, fetchTables, TableInfo, sendChatQuery } from "@/lib/api";
import { getStoredUser, type AppUser } from "@/lib/auth";
import { logAudit } from "@/lib/audit";

type ActiveView = "chat" | "explorer" | "reports" | "audit" | "settings" | "help";

const _WELCOME_FOLLOWS: Record<string, string[]> = {
  fraud_analyst: [
    "Show top 10 suspicious transactions this week",
    "What is the fraud rate by merchant category this month?",
    "Show accounts with active fraud alerts",
    "Which country has the highest fraud score trend?",
  ],
  retail_user: [
    "Show total spend by merchant category this month",
    "Which customers are overdue on payments?",
    "Show top 10 customers by MTD spend",
    "Show payment status distribution across all accounts",
  ],
  finance_user: [
    "Show portfolio KPIs this quarter",
    "What is the delinquency rate by country?",
    "Show MTD spend vs prior month across all segments",
    "Which legal entity has the highest revenue this month?",
  ],
  regional_finance_user: [
    "Show portfolio KPIs for each country this month",
    "Which country had the biggest MoM spend change?",
    "Show payment volume by country this quarter",
    "What is the regional delinquency rate compared to global average?",
  ],
  regional_risk_user: [
    "Show fraud rate by country and merchant category",
    "Which region has the highest delinquency rate?",
    "Show suspicious transactions by country this week",
    "What is the fraud trend by country over the last 3 months?",
  ],
  analyst: [
    "Show total spend by merchant category",
    "What is the fraud rate by merchant?",
    "Show payment volume trend by month",
    "Show monthly transaction count trend",
  ],
};

function makeWelcome(userName?: string, persona?: string): ChatMessage {
  const greeting = userName ? `Welcome back, **${userName}**!` : "Welcome to DataPrismAI";
  const key = (persona ?? "analyst").toLowerCase();
  const followUps = _WELCOME_FOLLOWS[key] ?? _WELCOME_FOLLOWS.analyst;
  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: `${greeting} — Your banking analytics platform is ready. Ask anything about your data.`,
    followUps,
  };
}

export function AppShell() {
  const [mounted, setMounted] = useState(false);
  const [user, setUser] = useState<AppUser | null>(null);
  const [persona, setPersona] = useState("analyst");
  const [theme, setTheme] = useState<"dark" | "dawn">("dark");
  const [messages, setMessages] = useState<ChatMessage[]>([makeWelcome()]);
  const [reports, setReports] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState<ActiveView>("chat");
  const [catalog, setCatalog] = useState<SemanticCatalogResponse | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [tablesDb, setTablesDb] = useState("banking");
  const [threadId, setThreadId] = useState<string | undefined>(undefined);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [queryHistory, setQueryHistory] = useState<{ query: string; metric: string; rowCount: number; ts: number }[]>([]);
  const [timeRange, setTimeRange] = useState<string>("ALL");
  const lastSentRef = useRef<{ message: string; time: number }>({ message: "", time: 0 });

  // ── Hydrate from localStorage after mount (avoids SSR mismatch) ─────────
  useEffect(() => {
    const u = getStoredUser();
    if (u) {
      setUser(u);
      setPersona(u.persona ?? "analyst");
      setMessages([makeWelcome(u.name, u.persona)]);
    }
    setMounted(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── If no user logged in, show login page ─────────────────────────────────
  if (!mounted) return null;

  if (!user) {
    return <LoginPanel onLogin={(u) => {
      setUser(u);
      setPersona(u.persona ?? "analyst");
      setMessages([makeWelcome(u.name, u.persona)]);
      logAudit("login", `${u.name} (${u.role}) logged in`, { userId: u.id, userName: u.name });
    }} />;
  }

  return <AppShellInner
    user={user}
    persona={persona}
    setPersona={setPersona}
    theme={theme}
    setTheme={setTheme}
    messages={messages}
    setMessages={setMessages}
    reports={reports}
    setReports={setReports}
    isLoading={isLoading}
    setIsLoading={setIsLoading}
    activeView={activeView}
    setActiveView={setActiveView}
    catalog={catalog}
    setCatalog={setCatalog}
    tables={tables}
    setTables={setTables}
    tablesDb={tablesDb}
    setTablesDb={setTablesDb}
    threadId={threadId}
    setThreadId={setThreadId}
    sidebarOpen={sidebarOpen}
    setSidebarOpen={setSidebarOpen}
    queryHistory={queryHistory}
    setQueryHistory={setQueryHistory}
    timeRange={timeRange}
    setTimeRange={setTimeRange}
    lastSentRef={lastSentRef}
    onLogout={() => {
      logAudit("logout", `${user.name} logged out`, { userId: user.id, userName: user.name });
      setUser(null);
      setMessages([makeWelcome()]);
    }}
  />;
}

// ── Inner shell (only rendered when logged in) ─────────────────────────────
type InnerProps = {
  user: AppUser;
  persona: string;
  setPersona: (p: string) => void;
  theme: "dark" | "dawn";
  setTheme: (t: "dark" | "dawn") => void;
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  reports: ChatMessage[];
  setReports: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  isLoading: boolean;
  setIsLoading: (l: boolean) => void;
  activeView: ActiveView;
  setActiveView: (v: ActiveView) => void;
  catalog: SemanticCatalogResponse | null;
  setCatalog: (c: SemanticCatalogResponse | null) => void;
  tables: TableInfo[];
  setTables: (t: TableInfo[]) => void;
  tablesDb: string;
  setTablesDb: (d: string) => void;
  threadId: string | undefined;
  setThreadId: (t: string | undefined) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (o: boolean) => void;
  queryHistory: { query: string; metric: string; rowCount: number; ts: number }[];
  setQueryHistory: React.Dispatch<React.SetStateAction<{ query: string; metric: string; rowCount: number; ts: number }[]>>;
  timeRange: string;
  setTimeRange: (t: string) => void;
  lastSentRef: React.MutableRefObject<{ message: string; time: number }>;
  onLogout: () => void;
};

function AppShellInner({
  user, persona, setPersona, theme, setTheme,
  messages, setMessages, reports, setReports,
  isLoading, setIsLoading, activeView, setActiveView,
  catalog, setCatalog, tables, setTables, tablesDb, setTablesDb,
  threadId, setThreadId, sidebarOpen, setSidebarOpen,
  queryHistory, setQueryHistory,
  timeRange, setTimeRange,
  lastSentRef, onLogout,
}: InnerProps) {

  useEffect(() => {
    fetchSemanticCatalog()
      .then(setCatalog)
      .catch((err) => console.error("Failed to load semantic catalog", err));
    fetchTables()
      .then(r => { setTables(r.tables); setTablesDb(r.database); })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Listen for canned report run events from ReportsPanel
  useEffect(() => {
    const handler = (e: Event) => {
      const query = (e as CustomEvent<string>).detail;
      if (query) { setActiveView("chat"); handleSend(query); }
    };
    window.addEventListener("dataprismai:query", handler);
    return () => window.removeEventListener("dataprismai:query", handler);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persona, threadId, isLoading]);

  useEffect(() => {
    document.documentElement.classList.toggle("theme-dawn", theme === "dawn");
    document.documentElement.classList.toggle("theme-dark", theme === "dark");
  }, [theme]);

  // Persona is auto-derived from role; no user UI to change it.
  // Kept here for future role-based persona updates on re-login.
  void setPersona;

  function handleNewChat() {
    setMessages([makeWelcome(user.name, user.persona)]);
    setThreadId(undefined);
    setActiveView("chat");
  }

  function handleViewChange(v: ActiveView) {
    setActiveView(v);
    logAudit("view_change", `Navigated to: ${v}`, { userId: user.id, userName: user.name });
  }

  async function handleSend(message: string) {
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;

    const now = Date.now();
    if (trimmed === lastSentRef.current.message && now - lastSentRef.current.time < 800) return;
    lastSentRef.current = { message: trimmed, time: now };

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    logAudit("chat_query", trimmed, { userId: user.id, userName: user.name });

    try {
      const response = await sendChatQuery(
        trimmed, persona, threadId, "default", [],
        user.country_codes ?? [],
        user.allowed_domains ?? [],
        timeRange,
      );
      if (response.thread_id) setThreadId(response.thread_id);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        threadId: response.thread_id,
        reportId: response.report_id,
        intentType: response.intent_type,
        responseMode: response.response_mode,
        literalTableName: response.literal_table_name,
        actions: response.actions,
        followUps: response.follow_ups,
        insights: response.insights,
        bottlenecks: response.bottlenecks,
        highlightActions: response.highlight_actions,
        kpiMetrics: response.kpi_metrics,
        insightRecommendations: response.insight_recommendations,
        assumptions: response.assumptions,
        chartConfig: response.chart_config,
        chartRecommendations: response.chart_recommendations,
        visualizationConfig: response.visualization_config,
        visualizationRecommendations: response.visualization_recommendations,
        sql: response.sql,
        sqlExplanation: response.sql_explanation,
        sqlValidationIssues: response.sql_validation_issues,
        resultColumns: response.result_columns,
        resultRows: response.result_rows,
        resultRowCount: response.result_row_count,
        resultEngine: response.result_engine,
        resultExecutionTimeMs: response.result_execution_time_ms,
        reasoningSteps: response.reasoning_steps,
        sqlLlmUsed: response.sql_llm_used,
        modelUsed: response.model_used,
        semanticContext: {
          metric: response.semantic_context?.metric,
          dimensions: response.semantic_context?.dimensions,
          engine: response.semantic_context?.engine,
          domain: response.semantic_context?.domain,
          definition: response.semantic_context?.definition,
          persona: response.semantic_context?.persona,
          promptTemplateLoaded: response.semantic_context?.prompt_template_loaded,
        },
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.result_row_count > 0) {
        setQueryHistory(prev => [{
          query: trimmed,
          metric: response.semantic_context?.metric ?? "Unknown",
          rowCount: response.result_row_count,
          ts: Date.now(),
        }, ...prev].slice(0, 100));
        setReports((prev) => [assistantMessage, ...prev].slice(0, 50));
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: "Sorry, DataPrismAI could not process your request right now." },
      ]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="h-screen overflow-hidden" style={{ backgroundColor: "var(--background)", color: "var(--foreground)" }}>
      <div className="flex h-full flex-col">
        <TopBar
          theme={theme}
          onThemeToggle={() => setTheme(theme === "dark" ? "dawn" : "dark")}
          userName={user.name}
          onLogout={onLogout}
          onHelpOpen={() => setActiveView("help")}
        />
        <div className="flex min-h-0 flex-1">
          <Sidebar
            activeView={activeView}
            onChangeView={handleViewChange}
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            onNewChat={handleNewChat}
            queryHistory={queryHistory}
            onHistoryQuery={(q) => { setActiveView("chat"); handleSend(q); }}
            workspaceName={user.name}
            persona={persona}
          />
          <section className="flex min-w-0 flex-1 flex-col overflow-hidden">
            {activeView === "chat" ? (
              <ChatWorkspace
                messages={messages}
                onSend={handleSend}
                isLoading={isLoading}
                persona={persona}
                userName={user.name}
                timeRange={timeRange}
                onTimeRangeChange={setTimeRange}
              />
            ) : activeView === "explorer" ? (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-6xl">
                  <ExplorerPanel
                    catalog={catalog}
                    tables={tables}
                    database={tablesDb}
                    queryHistory={queryHistory}
                    onQuerySend={(q) => { setActiveView("chat"); handleSend(q); }}
                  />
                </div>
              </div>
            ) : activeView === "reports" ? (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-6xl">
                  <ReportsPanel reports={reports} />
                </div>
              </div>
            ) : activeView === "audit" ? (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-6xl">
                  <AuditPanel />
                </div>
              </div>
            ) : activeView === "settings" ? (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-4xl">
                  <SettingsPanel
                    currentUser={user}
                    onThemeChange={setTheme}
                    currentTheme={theme}
                  />
                </div>
              </div>
            ) : activeView === "help" ? (
              <div className="flex-1 overflow-hidden">
                <HelpPanel />
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  );
}
