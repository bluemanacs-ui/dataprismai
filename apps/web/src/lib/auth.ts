"use client";
// ── Auth store (localStorage-backed, no backend auth yet) ─────────────────────

export type UserRole =
  | "fraud_analyst"
  | "retail_user"
  | "finance_user"
  | "regional_finance_user"
  | "regional_risk_user"
  | "admin";

export type AppUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  /** DB persona — maps directly to semantic_access_control.persona */
  persona: string;
  /** Display department label */
  department: string;
  /** Primary domain for this user */
  default_domain: string;
  /** Domains accessible per user_domain_mapping */
  allowed_domains: string[];
  country_codes: string[];
  avatar?: string;
};

// Role → display label
export const ROLE_LABEL: Record<UserRole, string> = {
  fraud_analyst:          "Fraud Analyst",
  retail_user:            "CC Operations",
  finance_user:           "Finance Analyst",
  regional_finance_user:  "Regional Finance",
  regional_risk_user:     "Regional Risk",
  admin:                  "Administrator",
};

// Role → persona (now 1:1 — kept for backward compat with app-shell)
export const ROLE_PERSONA_MAP: Record<UserRole, string> = {
  fraud_analyst:          "fraud_analyst",
  retail_user:            "retail_user",
  finance_user:           "finance_user",
  regional_finance_user:  "regional_finance_user",
  regional_risk_user:     "regional_risk_user",
  admin:                  "fraud_analyst",      // admin gets the broadest analytical persona
};

export const PERSONAS = [
  { value: "fraud_analyst",         label: "Fraud Analyst",         desc: "Risk + transaction-level investigation and fraud detection" },
  { value: "retail_user",           label: "CC Operations",         desc: "Spend, payments, customer-level retail card operations" },
  { value: "finance_user",          label: "Finance Analyst",       desc: "Portfolio KPIs, spend roll-ups, executive P&L view" },
  { value: "regional_finance_user", label: "Regional Finance",      desc: "Regional P&L, portfolio KPIs scoped to country" },
  { value: "regional_risk_user",    label: "Regional Risk",         desc: "Country-scoped risk metrics, transaction monitoring" },
];

// ── Demo users — aligned to semantic_access_control personas ─────────────────
// Passwords: admin → admin123, all others → pass123
export const DEMO_USERS: (AppUser & { password: string })[] = [
  {
    id: "u1",
    name: "Acs Admin",
    email: "admin@dataprismai.io",
    role: "admin",
    persona: "fraud_analyst",
    department: "Platform",
    default_domain: "risk",
    allowed_domains: ["customer", "transactions", "spend", "payments", "risk", "portfolio"],
    country_codes: ["SG", "MY", "IN"],
    password: "admin123",
  },
  {
    id: "u2",
    name: "Sarah Lee",
    email: "sarah@dataprismai.io",
    role: "fraud_analyst",
    persona: "fraud_analyst",
    department: "Risk",
    default_domain: "risk",
    allowed_domains: ["risk", "transactions", "customer"],
    country_codes: ["SG"],
    password: "pass123",
  },
  {
    id: "u3",
    name: "David Chen",
    email: "david@dataprismai.io",
    role: "retail_user",
    persona: "retail_user",
    department: "Credit Card",
    default_domain: "spend",
    allowed_domains: ["spend", "payments", "transactions", "customer"],
    country_codes: ["SG", "MY"],
    password: "pass123",
  },
  {
    id: "u4",
    name: "Priya Kapoor",
    email: "priya@dataprismai.io",
    role: "finance_user",
    persona: "finance_user",
    department: "Finance",
    default_domain: "portfolio",
    allowed_domains: ["portfolio", "spend", "payments"],
    country_codes: ["SG", "MY", "IN"],
    password: "pass123",
  },
  {
    id: "u5",
    name: "Elena Sousa",
    email: "elena@dataprismai.io",
    role: "regional_finance_user",
    persona: "regional_finance_user",
    department: "Regional Finance",
    default_domain: "portfolio",
    allowed_domains: ["portfolio", "spend"],
    country_codes: ["MY"],
    password: "pass123",
  },
  {
    id: "u6",
    name: "Mark Williams",
    email: "mark@dataprismai.io",
    role: "regional_risk_user",
    persona: "regional_risk_user",
    department: "Regional Risk",
    default_domain: "risk",
    allowed_domains: ["risk", "transactions", "customer"],
    country_codes: ["IN"],
    password: "pass123",
  },
];

const STORAGE_KEY = "dataprismai_user";

export function getStoredUser(): AppUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AppUser) : null;
  } catch {
    return null;
  }
}

export function storeUser(user: AppUser) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearUser() {
  localStorage.removeItem(STORAGE_KEY);
}

export function login(email: string, password: string): AppUser | null {
  const found = DEMO_USERS.find(
    (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password,
  );
  if (!found) return null;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { password: _pw, ...user } = found;
  storeUser(user);
  return user;
}
