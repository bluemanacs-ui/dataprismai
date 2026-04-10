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
  chatMode: string = "hybrid",
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
      chat_mode: chatMode,
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

export type ColumnProfile = {
  name: string;
  type: string;
  nullable: string;
  null_count: number;
  null_pct: number;
  distinct_count: number;
  fill_pct: number;
  min_val?: string | null;
  max_val?: string | null;
  avg_val?: string | null;
  top_values?: { value: string; count: number; pct: number }[];
};

export type TableProfile = {
  table: string;
  total_rows: number;
  total_columns: number;
  null_columns: number;
  columns: ColumnProfile[];
  error?: string;
};

export async function fetchTableProfile(tableName: string): Promise<TableProfile> {
  const res = await fetch(`${API_BASE_URL}/semantic/profiling/${encodeURIComponent(tableName)}`, { cache: "no-store" });
  if (!res.ok) return { table: tableName, total_rows: 0, total_columns: 0, null_columns: 0, columns: [], error: "Request failed" };
  return res.json();
}

// ── Data Dictionary ──────────────────────────────────────────────────────────

export type DicTable = {
  table_id: number;
  table_name: string;
  display_name: string;
  layer: string;
  domain: string;
  description: string;
  row_count_approx: number;
  owner: string;
  refresh_cadence: string;
};

export type DicColumn = {
  column_id: number;
  table_name: string;
  column_name: string;
  display_name: string;
  data_type: string;
  description: string;
  is_pii: number;
  is_nullable: number;
  is_primary_key: number;
  enum_values: string | null;
  business_rule: string | null;
  example_values: string | null;
};

export type DicRelationship = {
  rel_id: number;
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship_type: string;
  description: string;
};

export async function fetchDictionaryTables(layer?: string, domain?: string): Promise<{ tables: DicTable[]; error?: string }> {
  const params = new URLSearchParams();
  if (layer) params.set("layer", layer);
  if (domain) params.set("domain", domain);
  const qs = params.toString() ? `?${params}` : "";
  const res = await fetch(`${API_BASE_URL}/dictionary/tables${qs}`, { cache: "no-store" });
  if (!res.ok) return { tables: [], error: "Request failed" };
  return res.json();
}

export async function fetchDictionaryTableDetail(tableName: string): Promise<{ table: DicTable; columns: DicColumn[]; relationships: DicRelationship[]; error?: string }> {
  const res = await fetch(`${API_BASE_URL}/dictionary/tables/${encodeURIComponent(tableName)}`, { cache: "no-store" });
  if (!res.ok) return { table: {} as DicTable, columns: [], relationships: [], error: "Request failed" };
  return res.json();
}

export async function searchDictionary(q: string): Promise<{ query: string; tables: DicTable[]; columns: DicColumn[]; error?: string }> {
  const res = await fetch(`${API_BASE_URL}/dictionary/search?q=${encodeURIComponent(q)}`, { cache: "no-store" });
  if (!res.ok) return { query: q, tables: [], columns: [] };
  return res.json();
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

// ── Config API ───────────────────────────────────────────────────────────────

export type ConfigEntry = {
  key: string;
  label: string;
  description: string;
  value: string;
  default: string;
  input_type: "text" | "password" | "number" | "boolean" | "select" | "textarea";
  options: { value: string; label: string }[];
  is_readonly: boolean;
  is_sensitive: boolean;
  restart_req: boolean;
  overridden: boolean;
};

export type ConfigSection = {
  id: string;
  label: string;
  icon: string;
  description: string;
  entries: ConfigEntry[];
};

export type ConfigResponse = {
  sections: ConfigSection[];
  total_keys: number;
  overridden_keys: number;
};

export async function fetchConfig(): Promise<ConfigResponse> {
  const res = await fetch(`${API_BASE_URL}/config`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function patchConfig(updates: Record<string, string>): Promise<{ ok: boolean; saved: number }> {
  const res = await fetch(`${API_BASE_URL}/config`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ updates }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail ?? "Failed to save config");
  }
  return res.json();
}

export async function resetConfigKey(key: string): Promise<{ ok: boolean; key: string; reverted_to: string }> {
  const res = await fetch(`${API_BASE_URL}/config/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key }),
  });
  if (!res.ok) throw new Error("Failed to reset config key");
  return res.json();
}

export async function refreshConfig(): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE_URL}/config/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to refresh config");
  return res.json();
}
