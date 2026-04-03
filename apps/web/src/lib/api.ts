import {
  ChatApiResponse,
  SemanticCatalogResponse,
  SkillCatalogResponse,
} from "@/types/chat";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function sendChatQuery(message: string, persona: string) {
  const response = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      persona,
      workspace: "default",
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

export async function fetchSkillCatalog() {
  const response = await fetch(`${API_BASE_URL}/skills/catalog`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch skill catalog");
  }

  return (await response.json()) as SkillCatalogResponse;
}
