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

// Generalized visualization contract (v2 — from LangGraph nodes)
export type VisualizationPayload =
  | ChartConfig                                   // chart / bar / line / pie / donut
  | { nodes: unknown[]; edges: unknown[] }        // flow / dag
  | Record<string, unknown>;                      // table / metric / custom

export type VisualizationConfig = {
  visualization_type: "bar" | "line" | "pie" | "donut" | "area" | "flow" | "table" | "metric" | string;
  title: string;
  description: string;
  payload: VisualizationPayload;
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

export type ChartRecommendation = {
  id: string;
  label: string;
  reason: string;
  chart_config: ChartConfig;
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
  thread_id?: string;
  report_id?: string;
  intent_type: string;          // preview_data | schema_query | metric_query | insight_query | explanation | report
  response_mode: string;        // table | schema | metric | insight
  literal_table_name: string;   // explicit table name from user message
  insights: string[];
  bottlenecks: string[];
  highlight_actions: string[];
  kpi_metrics: { label: string; value: string; trend: string | null }[];
  insight_recommendations: string[];
  follow_ups: string[];
  assumptions: string[];
  actions: string[];
  chart_title: string;
  chart_type: string;
  chart_config: ChartConfig;
  chart_recommendations: ChartRecommendation[];
  visualization_config?: VisualizationConfig;
  visualization_recommendations?: VisualizationConfig[];
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
  reasoning_steps: string[];
  sql_llm_used: boolean;
  model_used?: string | null;
  raw_model_output?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  threadId?: string;
  reportId?: string;
  intentType?: string;        // preview_data | schema_query | metric_query | insight_query
  responseMode?: string;      // table | schema | metric | insight
  literalTableName?: string;  // explicit table name extracted from message
  actions?: string[];
  followUps?: string[];
  insights?: string[];
  bottlenecks?: string[];
  highlightActions?: string[];
  kpiMetrics?: { label: string; value: string; trend: string | null }[];
  insightRecommendations?: string[];
  assumptions?: string[];
  chartConfig?: ChartConfig;
  chartRecommendations?: ChartRecommendation[];
  visualizationConfig?: VisualizationConfig;
  visualizationRecommendations?: VisualizationConfig[];
  sql?: string;
  sqlExplanation?: string;
  sqlValidationIssues?: string[];
  resultColumns?: string[];
  resultRows?: Record<string, string | number | null>[];
  resultRowCount?: number;
  resultEngine?: string;
  resultExecutionTimeMs?: number;
  reasoningSteps?: string[];
  sqlLlmUsed?: boolean;
  modelUsed?: string | null;
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
  chartRecommendations?: ChartRecommendation[];
  sql?: string;
  sqlExplanation?: string;
  sqlValidationIssues?: string[];
  resultColumns?: string[];
  resultRows?: Record<string, string | number | null>[];
  resultRowCount?: number;
  resultEngine?: string;
  resultExecutionTimeMs?: number;
  insights?: string[];
  insightRecommendations?: string[];
  assumptions?: string[];
  rawModelOutput?: string | null;
  followUps?: string[];
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
