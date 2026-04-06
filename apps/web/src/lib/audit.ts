// ── Audit event logger (localStorage-backed) ─────────────────────────────────

export type AuditEventType =
  | "login"
  | "logout"
  | "chat_query"
  | "table_select"
  | "dataset_change"
  | "persona_change"
  | "view_change"
  | "report_download"
  | "settings_change";

export type AuditEvent = {
  id: string;
  ts: number;
  type: AuditEventType;
  userId?: string;
  userName?: string;
  detail: string;
  metadata?: Record<string, unknown>;
};

const STORAGE_KEY = "dataprismai_audit";
const MAX_EVENTS = 500;

export function logAudit(
  type: AuditEventType,
  detail: string,
  opts?: { userId?: string; userName?: string; metadata?: Record<string, unknown> },
) {
  if (typeof window === "undefined") return;
  const event: AuditEvent = {
    id: crypto.randomUUID(),
    ts: Date.now(),
    type,
    userId: opts?.userId,
    userName: opts?.userName,
    detail,
    metadata: opts?.metadata,
  };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const existing: AuditEvent[] = raw ? JSON.parse(raw) : [];
    const updated = [event, ...existing].slice(0, MAX_EVENTS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    /* ignore */
  }
}

export function getAuditLog(): AuditEvent[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuditEvent[]) : [];
  } catch {
    return [];
  }
}

export function clearAuditLog() {
  localStorage.removeItem(STORAGE_KEY);
}
