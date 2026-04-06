import {
  ChatApiResponse,
  SemanticCatalogResponse,
  SkillCatalogResponse,
} from "@/types/chat";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export async function sendChatQuery(
  message: string,
  persona: string,
  threadId?: string,
  workspaceId: string = "default",
  selectedTables?: string[],
  countryCodes?: string[],
  allowedDomains?: string[],
  timeRange: string = "ALL",
) {
  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      persona,
      workspace: workspaceId,
      workspace_id: workspaceId,
      thread_id: threadId ?? null,
      selected_tables: selectedTables ?? [],
      country_codes: countryCodes ?? [],
      allowed_domains: allowedDomains ?? [],
      time_range: timeRange,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch chat response");
  }

  return (await response.json()) as ChatApiResponse;
}

export async function fetchSemanticCatalog() {
  const response = await fetch(`${API_BASE_URL}/semantic/catalog`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch semantic catalog");
  }

  return (await response.json()) as SemanticCatalogResponse;
}

export async function fetchTables(): Promise<{ tables: TableInfo[]; database: string; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/semantic/tables`, {
    cache: "no-store",
  });
  if (!response.ok) return { tables: [], database: "unknown", error: "Request failed" };
  return response.json();
}

export type TableColumn = {
  name: string;
  type: string;
  nullable: string;
  key: string;
};

export type TableInfo = {
  name: string;
  columns: TableColumn[];
  row_count: number;
};

export async function fetchTableSample(tableName: string, limit = 10, offset = 0): Promise<{ rows: Record<string, string | null>[]; table: string; offset: number; limit: number; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/semantic/sample/${encodeURIComponent(tableName)}?limit=${limit}&offset=${offset}`, {
    cache: "no-store",
  });
  if (!response.ok) return { rows: [], table: tableName, offset, limit, error: "Request failed" };
  return response.json();
}

export async function fetchSuggestions(
  persona: string,
  metric: string,
  excludeRecs: string[],
  excludeFus: string[],
  answerSnippet: string = "",
): Promise<{ insight_recommendations: string[]; follow_ups: string[] }> {
  const response = await fetch(`${API_BASE_URL}/chat/suggestions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      persona,
      metric,
      answer_snippet: answerSnippet.slice(0, 400),
      exclude_recs: excludeRecs,
      exclude_fus: excludeFus,
    }),
  });
  if (!response.ok) return { insight_recommendations: [], follow_ups: [] };
  return response.json();
}
