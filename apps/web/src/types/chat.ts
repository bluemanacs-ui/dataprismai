export type ChatApiResponse = {
  answer: string;
  actions: string[];
  follow_ups: string[];
  chart_title: string;
  chart_type: string;
  sql: string;
  insights: string[];
  semantic_context: {
    metric?: string;
    dimensions?: string[];
    engine?: string;
    persona?: string;
    prompt_template_loaded?: string;
  };
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  actions?: string[];
  followUps?: string[];
};

export type AnalysisState = {
  chartTitle?: string;
  chartType?: string;
  sql?: string;
  insights?: string[];
  semanticContext?: {
    metric?: string;
    dimensions?: string[];
    engine?: string;
    persona?: string;
    promptTemplateLoaded?: string;
  };
};
