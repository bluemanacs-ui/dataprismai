export type ChatApiResponse = {
  answer: string;
  insights: string[];
  follow_ups: string[];
  assumptions: string[];
  actions: string[];
  chart_title: string;
  chart_type: string;
  sql: string;
  semantic_context: {
    metric?: string;
    dimensions?: string[];
    engine?: string;
    domain?: string;
    definition?: string;
    persona?: string;
    prompt_template_loaded?: string;
  };
  raw_model_output?: string | null;
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
  assumptions?: string[];
  rawModelOutput?: string | null;
  semanticContext?: {
    metric?: string;
    dimensions?: string[];
    engine?: string;
    domain?: string;
    definition?: string;
    persona?: string;
    promptTemplateLoaded?: string;
  };
};
