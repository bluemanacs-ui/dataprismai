"use client";

import { useState } from "react";
import { TopBar } from "@/components/layout/top-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { AnalysisPanel } from "@/components/analysis/analysis-panel";
import { AnalysisState, ChatMessage } from "@/types/chat";
import { sendChatQuery } from "@/lib/api";

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
        sql: response.sql,
        sqlExplanation: response.sql_explanation,
        sqlValidationIssues: response.sql_validation_issues,
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
          <Sidebar />
          <ChatWorkspace
            messages={messages}
            onSend={handleSend}
            isLoading={isLoading}
          />
          <AnalysisPanel analysis={analysis} />
        </div>
      </div>
    </main>
  );
}
