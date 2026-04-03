"use client";

import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { AnalysisPanel } from "@/components/analysis/analysis-panel";
import { ExplorerPanel } from "@/components/explorer/explorer-panel";
import { SkillsPanel } from "@/components/skills/skills-panel";
import {
  AnalysisState,
  ChatMessage,
  SemanticCatalogResponse,
  SkillCatalogResponse,
} from "@/types/chat";
import { fetchSemanticCatalog, fetchSkillCatalog, sendChatQuery } from "@/lib/api";

const initialMessages: ChatMessage[] = [
  {
    id: "1",
    role: "assistant",
    content:
      "Welcome to DataPrismAI. Ask anything about your business data, metrics, and trends.",
    actions: ["Show Examples"],
    followUps: [
      "Show revenue trend by region",
      "Compare margin by segment",
      "Top churn drivers this quarter",
    ],
  },
];

export function AppShell() {
  const [persona, setPersona] = useState("analyst");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [analysis, setAnalysis] = useState<AnalysisState>({});
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState<"chat" | "explorer" | "skills">("chat");
  const [catalog, setCatalog] = useState<SemanticCatalogResponse | null>(null);
  const [skillCatalog, setSkillCatalog] = useState<SkillCatalogResponse | null>(null);

  useEffect(() => {
    fetchSemanticCatalog()
      .then(setCatalog)
      .catch((err) => console.error("Failed to load semantic catalog", err));

    fetchSkillCatalog()
      .then(setSkillCatalog)
      .catch((err) => console.error("Failed to load skill catalog", err));
  }, []);

  async function handleSend(message: string) {
    const trimmed = message.trim();
    if (!trimmed) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setActiveView("chat");

    try {
      const response = await sendChatQuery(trimmed, persona);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        actions: response.actions,
        followUps: response.follow_ups,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setAnalysis({
        chartTitle: response.chart_title,
        chartType: response.chart_type,
        chartConfig: response.chart_config,
        sql: response.sql,
        sqlExplanation: response.sql_explanation,
        sqlValidationIssues: response.sql_validation_issues,
        resultColumns: response.result_columns,
        resultRows: response.result_rows,
        resultRowCount: response.result_row_count,
        resultEngine: response.result_engine,
        resultExecutionTimeMs: response.result_execution_time_ms,
        insights: response.insights,
        assumptions: response.assumptions,
        rawModelOutput: response.raw_model_output,
        semanticContext: {
          metric: response.semantic_context.metric,
          dimensions: response.semantic_context.dimensions,
          engine: response.semantic_context.engine,
          domain: response.semantic_context.domain,
          definition: response.semantic_context.definition,
          persona: response.semantic_context.persona,
          promptTemplateLoaded: response.semantic_context.prompt_template_loaded,
        },
      });
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          "Sorry, DataPrismAI could not process your request right now.",
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="h-screen bg-zinc-950 text-zinc-100">
      <div className="flex h-full flex-col">
        <TopBar persona={persona} onPersonaChange={setPersona} />
        <div className="flex min-h-0 flex-1">
          <Sidebar activeView={activeView} onChangeView={setActiveView} />
          <section className="flex min-w-0 flex-1 flex-col">
            {activeView === "chat" ? (
              <ChatWorkspace
                messages={messages}
                onSend={handleSend}
                isLoading={isLoading}
              />
            ) : activeView === "explorer" ? (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-5xl">
                  <ExplorerPanel catalog={catalog} />
                </div>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <div className="mx-auto max-w-5xl">
                  <SkillsPanel catalog={skillCatalog} />
                </div>
              </div>
            )}
          </section>
          <AnalysisPanel analysis={analysis} />
        </div>
      </div>
    </main>
  );
}
