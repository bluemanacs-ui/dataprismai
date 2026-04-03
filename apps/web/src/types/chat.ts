export type ChartSeries = {
  key: string;
  label: string;
};

export type ChartConfig = {
  chart_type: string;
  x_key: string;
  series: ChartSeries[];
  title: string;
  description: string;
  data: Record<string, string | number | null>[];
};

export type SemanticMetric = {
  name: string;
  keywords: string[];
  dimensions: string[];
  engine: string;
  domain: string;
  definition: string;
};

export type SemanticDimension = {
  name: string;
  keywords: string[];
};

export type SemanticCatalogResponse = {
  metrics: SemanticMetric[];
  dimensions: SemanticDimension[];
};

export type SkillItem = {
  name: string;
  title: string;
  version: string;
  status: string;
  owner: string;
  description: string;
  scope: string[];
  guardrails: string[];
};

export type SkillCatalogResponse = {
  skills: SkillItem[];
};

export type ChatApiResponse = {
  answer: string;
  insights: string[];
  follow_ups: string[];
  assumptions: string[];
  actions: string[];
  chart_title: string;
  chart_type: string;
  chart_config: ChartConfig;
  sql: string;
  sql_explanation: string;
  sql_validation_issues: string[];
  result_columns: string[];
  result_rows: Record<string, string | number | null>[];
  result_row_count: number;
  result_engine: string;
  result_execution_time_ms: number;
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
  insights?: string[];
  assumptions?: string[];
  chartConfig?: ChartConfig;
  sql?: string;
  sqlExplanation?: string;
  sqlValidationIssues?: string[];
  resultColumns?: string[];
  resultRows?: Record<string, string | number | null>[];
  resultRowCount?: number;
  resultEngine?: string;
  resultExecutionTimeMs?: number;
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

export type AnalysisState = {
  chartTitle?: string;
  chartType?: string;
  chartConfig?: ChartConfig;
  sql?: string;
  sqlExplanation?: string;
  sqlValidationIssues?: string[];
  resultColumns?: string[];
  resultRows?: Record<string, string | number | null>[];
  resultRowCount?: number;
  resultEngine?: string;
  resultExecutionTimeMs?: number;
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
