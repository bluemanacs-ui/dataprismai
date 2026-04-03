# DataPrismAI Project Brief

## Product Name
DataPrismAI

## Primary Objective
Build a powerful, enterprise-grade GenBI insight data chatbot that enables users to explore, analyze, and understand complex business data through natural language, while the end-to-end development lifecycle is governed through BMAD and modular `SKILL.md`-driven execution.

## Core Goals
- Conversational analytics over enterprise data
- Insight generation, charting, recommendations, and explanation
- Governed semantic layer for metrics, dimensions, and joins
- Support for large datasets and complex joins
- Trino for federation and exploration
- StarRocks for low-latency serving
- Local LLM-enabled development and inference where practical
- Agent-driven software delivery with BMAD and skills

## Users
- Executives
- Business managers
- Data analysts
- Product managers
- Data engineers

## Product Principles
- Insight over raw query output
- Governed semantics over guessed business logic
- Trust and explainability over flashy demos
- Story-based incremental development over full rewrites
- Skill modularity over monolithic agent behavior

==============================


Perfect — now let’s make **DataPrismAI persona-aware**.

In this step we’ll add:

* persona prompt templates in the backend
* persona-aware mock response behavior
* the selected persona flowing through the app
* visibly different output styles for Analyst, CFO, Manager, Product, Engineer

This gives you the first real version of **customized prompting behavior** before plugging in a local LLM.

---

## 1. Create persona prompt files

From repo root:

```bash
cd ~/workspace/dataprismai
mkdir -p apps/api/app/prompts/personas
touch apps/api/app/prompts/__init__.py
touch apps/api/app/prompts/personas/__init__.py
```

Create `apps/api/app/prompts/personas/analyst.txt`:

```txt
Persona: Data Analyst

Behavior:
- Provide detailed analytical summaries
- Include breakdowns and useful next-step exploration
- Be comfortable showing SQL and assumptions
- Focus on metrics, dimensions, and drilldowns

Output style:
- Summary
- Key highlights
- Suggested analytical next steps
```

Create `apps/api/app/prompts/personas/cfo.txt`:

```txt
Persona: CFO

Behavior:
- Focus on executive-level financial insights
- Highlight business risk, variance, and performance
- Keep the answer concise and high-value
- Emphasize implications and recommendations

Output style:
- Executive summary
- Risks
- Recommendations
```

Create `apps/api/app/prompts/personas/manager.txt`:

```txt
Persona: Business Manager

Behavior:
- Focus on operational performance and actionability
- Use simple language
- Avoid technical detail unless necessary
- Prioritize practical next actions

Output style:
- Summary
- Key performance highlights
- Actionable next steps
```

Create `apps/api/app/prompts/personas/product.txt`:

```txt
Persona: Product Manager

Behavior:
- Focus on user behavior, growth, and experimentation
- Suggest segmentation, cohorts, and opportunity areas
- Connect changes to product decisions

Output style:
- Summary
- Product/growth insights
- Suggested experiments
```

Create `apps/api/app/prompts/personas/engineer.txt`:

```txt
Persona: Data Engineer

Behavior:
- Focus on correctness, SQL, data quality, and performance
- Explain assumptions and execution context
- Be precise and technical

Output style:
- Technical summary
- SQL/execution notes
- Data caveats
```

---

## 2. Add a persona prompt loader

Create `apps/api/app/prompts/persona_loader.py`:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "personas"


def load_persona_prompt(persona: str) -> str:
    safe_persona = (persona or "analyst").strip().lower()
    file_path = BASE_DIR / f"{safe_persona}.txt"

    if not file_path.exists():
        file_path = BASE_DIR / "analyst.txt"

    return file_path.read_text(encoding="utf-8")
```

---

## 3. Add persona-aware response generation

Replace `apps/api/app/services/chat_service.py` with:

```python
from app.prompts.persona_loader import load_persona_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse


def _build_answer(message: str, persona: str) -> tuple[str, list[str], list[str], list[str]]:
    persona = (persona or "analyst").lower()

    if persona == "cfo":
        answer = (
            f"Executive summary for: '{message}'\n\n"
            "Revenue increased 14.2% over the selected period. West region was the primary growth contributor, "
            "while South region remained nearly flat.\n\n"
            "The main business implication is concentration risk in growth performance, with over-reliance on one region."
        )
        actions = ["Show SQL", "Explain Metric", "View Risk Drivers", "Drill Down"]
        follow_ups = [
            "Show margin trend",
            "Highlight business risks",
            "Compare quarterly variance",
        ]
        insights = [
            "Revenue grew 14.2% over the period.",
            "Growth is concentrated in West region.",
            "South region stagnation could affect future performance.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "manager":
        answer = (
            f"Performance summary for: '{message}'\n\n"
            "Revenue is up 14.2%. West region is performing strongest, while South region needs attention.\n\n"
            "This suggests one strong growth area and one underperforming area that may require action."
        )
        actions = ["Show SQL", "Explain", "Drill Down", "View Recommendations"]
        follow_ups = [
            "Analyze South region",
            "Compare by team or segment",
            "Show action opportunities",
        ]
        insights = [
            "West region is the top performer.",
            "South region may need corrective action.",
            "Results suggest uneven regional performance.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "product":
        answer = (
            f"Product insight summary for: '{message}'\n\n"
            "Revenue increased 14.2%, with strongest contribution from West region. "
            "This may indicate stronger acquisition, conversion, or retention in that area.\n\n"
            "South region appears flat and is a candidate for deeper cohort or funnel analysis."
        )
        actions = ["Show SQL", "Explain", "View Segments", "Suggest Experiments"]
        follow_ups = [
            "Break down by acquisition channel",
            "Compare retention by region",
            "Suggest product experiments",
        ]
        insights = [
            "Growth may be tied to stronger regional behavior patterns.",
            "South region is a candidate for funnel analysis.",
            "Segment-level analysis is recommended.",
        ]
        return answer, actions, follow_ups, insights

    if persona == "engineer":
        answer = (
            f"Technical summary for: '{message}'\n\n"
            "The query indicates 14.2% revenue growth over the selected period. "
            "West region is the dominant contributor and South region remains nearly flat.\n\n"
            "This response is based on a mock semantic mapping using Revenue grouped by Month and Region."
        )
        actions = ["Show SQL", "Explain Join Path", "Inspect Semantic Context", "Drill Down"]
        follow_ups = [
            "Show execution assumptions",
            "Inspect metric definition",
            "Review SQL plan",
        ]
        insights = [
            "Semantic mapping used Revenue, Region, and Month.",
            "StarRocks is the current mock execution target.",
            "SQL and join behavior should be reviewed in live mode.",
        ]
        return answer, actions, follow_ups, insights

    answer = (
        f"Analytical summary for: '{message}'\n\n"
        "Revenue increased 14.2% over the selected period. West region contributed the strongest growth, "
        "while South remained nearly flat.\n\n"
        "This suggests a strong regional concentration pattern and a useful opportunity for deeper drilldown."
    )
    actions = ["Show SQL", "Explain", "Change Chart", "Drill Down"]
    follow_ups = [
        "Compare by segment",
        "Analyze South region",
        "Show monthly contribution",
    ]
    insights = [
        "Revenue is up 14.2% over the selected period.",
        "West region is the strongest contributor.",
        "South region may require investigation.",
    ]
    return answer, actions, follow_ups, insights


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    persona_prompt = load_persona_prompt(persona)
    answer, actions, follow_ups, insights = _build_answer(message, persona)

    return ChatQueryResponse(
        answer=answer,
        actions=actions,
        follow_ups=follow_ups,
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        insights=insights,
        semantic_context={
            "metric": "Revenue",
            "dimensions": ["Region", "Month"],
            "engine": "StarRocks",
            "persona": persona,
            "prompt_template_loaded": persona_prompt.splitlines()[0],
        },
    )
```

---

## 4. Keep the API route as-is

No change needed in:

* `apps/api/app/api/chat.py`
* `apps/api/app/schemas/chat.py`

Your existing route structure is already fine.

---

## 5. Improve the frontend persona labels

Right now your persona values are lowercase, which is correct for the API, but let’s display them cleanly in the analysis panel too.

Replace `apps/web/src/components/analysis/analysis-tabs.tsx` with this updated version:

```tsx
import { AnalysisState } from "@/types/chat";

type AnalysisTabsProps = {
  analysis: AnalysisState;
};

function formatPersona(persona?: string) {
  if (!persona) return "N/A";
  const map: Record<string, string> = {
    analyst: "Analyst",
    cfo: "CFO",
    manager: "Manager",
    product: "Product",
    engineer: "Engineer",
  };
  return map[persona] || persona;
}

export function AnalysisTabs({ analysis }: AnalysisTabsProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-800 px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {["Chart", "SQL", "Insights", "Semantic", "Lineage"].map((tab) => (
            <button
              key={tab}
              className={`rounded-full px-3 py-1.5 text-xs ${
                tab === "Chart"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4 overflow-y-auto p-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-3 text-sm font-semibold">Chart Preview</div>
          <div className="mb-3 text-xs text-zinc-500">
            {analysis.chartTitle || "No chart yet"} · {analysis.chartType || "N/A"}
          </div>
          <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-500">
            Chart rendering comes next
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">SQL</div>
          <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-300">
            {analysis.sql || "No SQL yet"}
          </pre>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Insights</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {(analysis.insights || ["No insights yet"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Semantic Context</div>
          <div className="space-y-2 text-sm text-zinc-300">
            <div>
              <span className="text-zinc-500">Metric:</span>{" "}
              {analysis.semanticContext?.metric || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Dimensions:</span>{" "}
              {analysis.semanticContext?.dimensions?.join(", ") || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Engine:</span>{" "}
              {analysis.semanticContext?.engine || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Persona:</span>{" "}
              {formatPersona(analysis.semanticContext?.persona)}
            </div>
            <div>
              <span className="text-zinc-500">Template:</span>{" "}
              {analysis.semanticContext?.promptTemplateLoaded || "N/A"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 6. Update the frontend type for the new field

Replace `apps/web/src/types/chat.ts` with:

```tsx
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
```

---

## 7. Map backend field names cleanly in AppShell

Replace `apps/web/src/components/ui-shell/app-shell.tsx` with this slightly updated version:

```tsx
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
        insights: response.insights,
        semanticContext: {
          metric: response.semantic_context.metric,
          dimensions: response.semantic_context.dimensions,
          engine: response.semantic_context.engine,
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
```

---

## 8. Run and test persona switching

Backend:

```bash
cd ~/workspace/dataprismai/apps/api
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd ~/workspace/dataprismai/apps/web
npm run dev
```

Now in the UI:

* choose **CFO**
* ask: `Show revenue trend by region`
* then choose **Engineer**
* ask the same thing again

You should see noticeably different answer styles and follow-ups.

---

## 9. Add BMAD story for this step

Create `bmad/stories/S4-persona-aware-prompting.md`:

```md
# Story S4: Persona-Aware Prompting

## Goal
Add persona-aware response generation to DataPrismAI so answers differ by user role.

## Scope
- backend persona templates
- persona template loader
- persona-aware response generation
- frontend display of selected persona and loaded template

## Files likely impacted
- apps/api/app/prompts/personas/*
- apps/api/app/prompts/persona_loader.py
- apps/api/app/services/chat_service.py
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx
- apps/web/src/types/chat.ts

## Out of scope
- real LLM integration
- semantic retrieval
- SQL generation logic changes
- authentication

## Acceptance Criteria
- persona templates exist
- selected persona influences answer style
- analysis panel shows persona context
- CFO, Analyst, Manager, Product, and Engineer responses differ meaningfully
```

---

## 10. Commit it

From repo root:

```bash
cd ~/workspace/dataprismai
git add .
git commit -m "feat: add persona-aware prompting flow"
```

---

## What comes next

The next best step is to add the **first local LLM integration** so DataPrismAI stops using hardcoded mock responses and starts generating persona-aware answers from a local model.

Given your RTX 4060 Laptop GPU with 8 GB VRAM, the practical next move is:

* install and verify Ollama
* pull a 7B-class model
* wire FastAPI chat service to Ollama
* keep everything else the same

That will be your first real AI backend.


===========================================


Great — now let’s connect **DataPrismAI** to a **real local LLM**.

Since your laptop has an **RTX 4060 Laptop GPU with 8 GB VRAM**, the safest practical path is:

* **Ollama**
* start with a **7B-class model**
* keep the current persona flow
* replace the hardcoded backend response with a real model call

Ollama’s docs describe local model serving, and their Docker docs cover running Ollama in containers with GPU support on Linux/WSL setups.

## 1. Install Ollama

The simplest path on your setup is to run Ollama **inside WSL/Linux** or via Docker after GPU passthrough is verified. Ollama’s docs include Linux install instructions and Docker usage.

In WSL, run:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then verify:

```bash
ollama --version
```

## 2. Start Ollama

Run:

```bash
ollama serve
```

Keep that terminal open for now.

By default, Ollama serves on:

```text
http://localhost:11434
```

## 3. Pull a practical starter model

For your GPU, start with a 7B instruct model.

A good practical first choice:

```bash
ollama pull qwen2.5:7b
```

If that tag is unavailable in your environment, check available model tags in the Ollama library and use the closest 7B instruct variant. Ollama’s library and docs are the source of truth for available model names.

Also pull a small embedding model for later:

```bash
ollama pull nomic-embed-text
```

## 4. Quick test the model

In another WSL terminal:

```bash
ollama run qwen2.5:7b "Give a short business summary of revenue increasing 14.2% with West region strongest and South flat."
```

If you get a sensible response, your local model path is working.

## 5. Add the Ollama Python client

In your API venv:

```bash
cd ~/workspace/dataprismai/apps/api
source .venv/bin/activate
pip install ollama
pip freeze > requirements.txt
```

Now open `apps/api/requirements.txt` and make sure it contains at least:

```txt
fastapi
uvicorn[standard]
pydantic
python-dotenv
ollama
```

## 6. Add API config for Ollama

Create `apps/api/app/core/config.py`:

```python
import os


class Settings:
    app_name: str = os.getenv("APP_NAME", "DataPrismAI API")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


settings = Settings()
```

Create `apps/api/.env`:

```env
APP_NAME=DataPrismAI API
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

## 7. Create a prompt builder

Create `apps/api/app/prompts/prompt_builder.py`:

```python
from app.prompts.persona_loader import load_persona_prompt


def build_chat_prompt(message: str, persona: str, semantic_context: dict | None = None) -> str:
    persona_text = load_persona_prompt(persona)
    semantic_context = semantic_context or {}

    metric = semantic_context.get("metric", "Revenue")
    dimensions = ", ".join(semantic_context.get("dimensions", ["Region", "Month"]))
    engine = semantic_context.get("engine", "StarRocks")

    return f"""
You are DataPrismAI, an enterprise GenBI insight assistant.

{persona_text}

Application rules:
- Be concise, useful, and business-relevant
- Do not expose hidden chain-of-thought
- Provide a reasoning summary, not private reasoning
- Stay grounded in the provided semantic context
- If assumptions are needed, state them briefly
- Do not invent unavailable data fields

Semantic context:
- Metric: {metric}
- Dimensions: {dimensions}
- Engine: {engine}

User question:
{message}

Return:
1. Main answer
2. 3 key insights
3. 3 suggested follow-up questions
""".strip()
```

## 8. Create the Ollama service

Create `apps/api/app/services/llm_service.py`:

```python
from ollama import Client
from app.core.config import settings


client = Client(host=settings.ollama_host)


def generate_with_ollama(prompt: str) -> str:
    response = client.generate(
        model=settings.ollama_model,
        prompt=prompt,
        stream=False,
        options={
            "temperature": 0.2,
        },
    )
    return response["response"].strip()
```

## 9. Replace the hardcoded chat service with real LLM generation

Replace `apps/api/app/services/chat_service.py` with:

```python
from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import generate_with_ollama


def _default_semantic_context(persona: str) -> dict:
    return {
        "metric": "Revenue",
        "dimensions": ["Region", "Month"],
        "engine": "StarRocks",
        "persona": persona,
    }


def _extract_followups(message: str, persona: str) -> list[str]:
    persona = (persona or "analyst").lower()

    if persona == "cfo":
        return [
            "Show margin trend",
            "Highlight business risks",
            "Compare quarterly variance",
        ]
    if persona == "manager":
        return [
            "Analyze South region",
            "Compare by segment",
            "Show recommended actions",
        ]
    if persona == "product":
        return [
            "Break down by acquisition channel",
            "Compare retention by region",
            "Suggest product experiments",
        ]
    if persona == "engineer":
        return [
            "Inspect semantic mapping",
            "Show SQL plan",
            "Review data assumptions",
        ]
    return [
        "Compare by segment",
        "Analyze South region",
        "Show monthly contribution",
    ]


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = _default_semantic_context(persona)
    prompt = build_chat_prompt(message, persona, semantic_context)
    llm_answer = generate_with_ollama(prompt)

    return ChatQueryResponse(
        answer=llm_answer,
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        follow_ups=_extract_followups(message, persona),
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        insights=[
            "Revenue is up over the selected period.",
            "West region appears strongest.",
            "South region may require investigation.",
        ],
        semantic_context={
            "metric": semantic_context["metric"],
            "dimensions": semantic_context["dimensions"],
            "engine": semantic_context["engine"],
            "persona": persona,
            "prompt_template_loaded": f"Persona: {persona.capitalize()}",
        },
    )
```

The function name stays the same so your route does not need to change yet.

## 10. Make sure FastAPI loads `.env`

Install dotenv already present in requirements. Update `apps/api/main.py`:

```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router

app = FastAPI(title="DataPrismAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "DataPrismAI API"}
```

## 11. Run everything

Terminal 1, Ollama:

```bash
ollama serve
```

Terminal 2, API:

```bash
cd ~/workspace/dataprismai/apps/api
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 3, web:

```bash
cd ~/workspace/dataprismai/apps/web
npm run dev
```

Now open:

```text
http://localhost:3000
```

Try:

* persona = **CFO**
* prompt = `Show revenue trend by region for the last 12 months`

Then:

* persona = **Engineer**
* same prompt

You should now get a real local-model-generated answer, not the previous hardcoded one.

## 12. Add error fallback so the app doesn’t break if Ollama is down

Update `apps/api/app/services/llm_service.py`:

```python
from ollama import Client
from app.core.config import settings


client = Client(host=settings.ollama_host)


def generate_with_ollama(prompt: str) -> str:
    try:
        response = client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": 0.2,
            },
        )
        return response["response"].strip()
    except Exception as exc:
        return (
            "DataPrismAI could not reach the local model runtime. "
            f"Ollama error: {exc}"
        )
```

That gives you a graceful failure mode.

## 13. Add BMAD story for this step

Create `bmad/stories/S5-local-llm-integration.md`:

```md
# Story S5: Local LLM Integration

## Goal
Replace mock backend response generation with a real local LLM using Ollama.

## Scope
- install and configure Ollama
- add backend config for local model host and model name
- create prompt builder
- add Ollama service wrapper
- connect chat service to local LLM

## Files likely impacted
- apps/api/app/core/config.py
- apps/api/app/prompts/prompt_builder.py
- apps/api/app/services/llm_service.py
- apps/api/app/services/chat_service.py
- apps/api/main.py
- apps/api/requirements.txt
- apps/api/.env

## Out of scope
- real NL-to-SQL
- chart rendering
- semantic retrieval
- query execution

## Acceptance Criteria
- Ollama runs locally
- API can call local model
- chat endpoint returns model-generated text
- persona-aware prompt flow remains intact
```

## 14. Commit it

From repo root:

```bash
cd ~/workspace/dataprismai
git add .
git commit -m "feat: integrate local Ollama model for chat responses"
```

## What comes next

The next right step is to make the app more structured by introducing the first **real GenBI response contract**:

* structured JSON output from the model
* separate fields for answer, insights, follow-ups, assumptions
* better parsing and safer UI rendering

That is the bridge from “LLM chat” to “real GenBI app behavior.”


================================

Perfect — and yes, if your frontend is on **port 3001**, use:

```text
http://localhost:3001
```

and update any frontend/backend allowlist or env values accordingly.

Now let’s move to the next important step:

## Step: make DataPrismAI return a structured GenBI response

Right now the model returns one big text blob.
We want it to return **structured fields** like:

* answer
* insights
* follow-ups
* assumptions
* chart hint

That makes the app much more reliable and easier to evolve.

---

## 1. Update backend response schema

Replace `apps/api/app/schemas/chat.py` with:

```python
from pydantic import BaseModel, Field
from typing import List, Optional


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: str = Field(default="analyst")
    workspace: str = Field(default="default")


class ChatQueryResponse(BaseModel):
    answer: str
    insights: List[str]
    follow_ups: List[str]
    assumptions: List[str]
    actions: List[str]
    chart_title: str
    chart_type: str
    sql: str
    semantic_context: dict
    raw_model_output: Optional[str] = None
```

---

## 2. Strengthen the prompt for structured output

Replace `apps/api/app/prompts/prompt_builder.py` with:

```python
from app.prompts.persona_loader import load_persona_prompt


def build_chat_prompt(message: str, persona: str, semantic_context: dict | None = None) -> str:
    persona_text = load_persona_prompt(persona)
    semantic_context = semantic_context or {}

    metric = semantic_context.get("metric", "Revenue")
    dimensions = ", ".join(semantic_context.get("dimensions", ["Region", "Month"]))
    engine = semantic_context.get("engine", "StarRocks")

    return f"""
You are DataPrismAI, an enterprise GenBI insight assistant.

{persona_text}

Application rules:
- Be concise, useful, and business-relevant
- Do not expose hidden chain-of-thought
- Provide a reasoning summary, not private reasoning
- Stay grounded in the provided semantic context
- If assumptions are needed, state them briefly
- Do not invent unavailable data fields
- Output valid JSON only
- Do not wrap JSON in markdown fences

Semantic context:
- Metric: {metric}
- Dimensions: {dimensions}
- Engine: {engine}

User question:
{message}

Return JSON with exactly this shape:
{{
  "answer": "string",
  "insights": ["string", "string", "string"],
  "follow_ups": ["string", "string", "string"],
  "assumptions": ["string", "string"]
}}
""".strip()
```

---

## 3. Add safe JSON parsing helper

Create `apps/api/app/services/response_parser.py`:

````python
import json


def parse_model_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No valid JSON object found in model output")

    json_text = text[start:end + 1]
    return json.loads(json_text)
````

---

## 4. Update chat service to use structured model output

Replace `apps/api/app/services/chat_service.py` with:

```python
from app.prompts.prompt_builder import build_chat_prompt
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.llm_service import generate_with_ollama
from app.services.response_parser import parse_model_json


def _default_semantic_context(persona: str) -> dict:
    return {
        "metric": "Revenue",
        "dimensions": ["Region", "Month"],
        "engine": "StarRocks",
        "persona": persona,
    }


def _fallback_response(raw_output: str, persona: str, semantic_context: dict) -> ChatQueryResponse:
    return ChatQueryResponse(
        answer=raw_output or "DataPrismAI could not generate a structured response.",
        insights=[
            "Structured parsing failed.",
            "The local model returned unstructured output.",
            "Fallback response has been used.",
        ],
        follow_ups=[
            "Compare by segment",
            "Analyze South region",
            "Show monthly contribution",
        ],
        assumptions=[
            "Default semantic context was used.",
            "No real query execution has happened yet.",
        ],
        actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
        chart_title="Revenue Trend by Region",
        chart_type="line",
        sql=(
            "SELECT month, region, SUM(revenue) AS revenue\n"
            "FROM sales\n"
            "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
            "GROUP BY month, region\n"
            "ORDER BY month ASC;"
        ),
        semantic_context={
            "metric": semantic_context["metric"],
            "dimensions": semantic_context["dimensions"],
            "engine": semantic_context["engine"],
            "persona": persona,
            "prompt_template_loaded": f"Persona: {persona.capitalize()}",
        },
        raw_model_output=raw_output,
    )


def generate_mock_chat_response(payload: ChatQueryRequest) -> ChatQueryResponse:
    message = payload.message.strip()
    persona = payload.persona.strip().lower()

    semantic_context = _default_semantic_context(persona)
    prompt = build_chat_prompt(message, persona, semantic_context)
    raw_output = generate_with_ollama(prompt)

    try:
        parsed = parse_model_json(raw_output)

        answer = parsed.get("answer", "").strip()
        insights = parsed.get("insights", [])
        follow_ups = parsed.get("follow_ups", [])
        assumptions = parsed.get("assumptions", [])

        if not answer:
            raise ValueError("Missing answer in parsed response")

        return ChatQueryResponse(
            answer=answer,
            insights=insights[:5] if isinstance(insights, list) else [],
            follow_ups=follow_ups[:5] if isinstance(follow_ups, list) else [],
            assumptions=assumptions[:5] if isinstance(assumptions, list) else [],
            actions=["Show SQL", "Explain", "Change Chart", "Drill Down"],
            chart_title="Revenue Trend by Region",
            chart_type="line",
            sql=(
                "SELECT month, region, SUM(revenue) AS revenue\n"
                "FROM sales\n"
                "WHERE month >= CURRENT_DATE - INTERVAL '12 months'\n"
                "GROUP BY month, region\n"
                "ORDER BY month ASC;"
            ),
            semantic_context={
                "metric": semantic_context["metric"],
                "dimensions": semantic_context["dimensions"],
                "engine": semantic_context["engine"],
                "persona": persona,
                "prompt_template_loaded": f"Persona: {persona.capitalize()}",
            },
            raw_model_output=raw_output,
        )
    except Exception:
        return _fallback_response(raw_output, persona, semantic_context)
```

---

## 5. Update frontend types

Replace `apps/web/src/types/chat.ts` with:

```tsx
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
    persona?: string;
    promptTemplateLoaded?: string;
  };
};
```

---

## 6. Update AppShell mapping

Replace `apps/web/src/components/ui-shell/app-shell.tsx` with:

```tsx
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
        insights: response.insights,
        assumptions: response.assumptions,
        rawModelOutput: response.raw_model_output,
        semanticContext: {
          metric: response.semantic_context.metric,
          dimensions: response.semantic_context.dimensions,
          engine: response.semantic_context.engine,
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
```

---

## 7. Show assumptions in analysis panel

Replace `apps/web/src/components/analysis/analysis-tabs.tsx` with:

```tsx
import { AnalysisState } from "@/types/chat";

type AnalysisTabsProps = {
  analysis: AnalysisState;
};

function formatPersona(persona?: string) {
  if (!persona) return "N/A";
  const map: Record<string, string> = {
    analyst: "Analyst",
    cfo: "CFO",
    manager: "Manager",
    product: "Product",
    engineer: "Engineer",
  };
  return map[persona] || persona;
}

export function AnalysisTabs({ analysis }: AnalysisTabsProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-zinc-800 px-4 py-3">
        <div className="flex flex-wrap gap-2">
          {["Chart", "SQL", "Insights", "Semantic", "Lineage"].map((tab) => (
            <button
              key={tab}
              className={`rounded-full px-3 py-1.5 text-xs ${
                tab === "Chart"
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4 overflow-y-auto p-4">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-3 text-sm font-semibold">Chart Preview</div>
          <div className="mb-3 text-xs text-zinc-500">
            {analysis.chartTitle || "No chart yet"} · {analysis.chartType || "N/A"}
          </div>
          <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-500">
            Chart rendering comes next
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">SQL</div>
          <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-zinc-300">
            {analysis.sql || "No SQL yet"}
          </pre>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Insights</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {(analysis.insights || ["No insights yet"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Assumptions</div>
          <ul className="space-y-2 text-sm text-zinc-300">
            {(analysis.assumptions || ["No assumptions yet"]).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="mb-2 text-sm font-semibold">Semantic Context</div>
          <div className="space-y-2 text-sm text-zinc-300">
            <div>
              <span className="text-zinc-500">Metric:</span>{" "}
              {analysis.semanticContext?.metric || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Dimensions:</span>{" "}
              {analysis.semanticContext?.dimensions?.join(", ") || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Engine:</span>{" "}
              {analysis.semanticContext?.engine || "N/A"}
            </div>
            <div>
              <span className="text-zinc-500">Persona:</span>{" "}
              {formatPersona(analysis.semanticContext?.persona)}
            </div>
            <div>
              <span className="text-zinc-500">Template:</span>{" "}
              {analysis.semanticContext?.promptTemplateLoaded || "N/A"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 8. If your frontend is on port 3001, make sure backend CORS matches

Update `apps/api/main.py`:

```python
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router

app = FastAPI(title="DataPrismAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "DataPrismAI API"}
```

Also make sure `apps/web/.env.local` still points to:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 9. Restart services

API:

```bash
cd ~/workspace/dataprismai/apps/api
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Web:

```bash
cd ~/workspace/dataprismai/apps/web
npm run dev -- --port 3001
```

Ollama:

```bash
ollama serve
```

Now open:

```text
http://localhost:3001
```

---

## 10. Add BMAD story for this step

Create `bmad/stories/S6-structured-genbi-response.md`:

```md
# Story S6: Structured GenBI Response

## Goal
Move DataPrismAI from freeform LLM output to structured GenBI response fields.

## Scope
- JSON-based model prompt contract
- backend JSON parsing
- fallback handling
- frontend rendering of assumptions and structured fields

## Files likely impacted
- apps/api/app/prompts/prompt_builder.py
- apps/api/app/services/response_parser.py
- apps/api/app/services/chat_service.py
- apps/api/app/schemas/chat.py
- apps/api/main.py
- apps/web/src/types/chat.ts
- apps/web/src/components/ui-shell/app-shell.tsx
- apps/web/src/components/analysis/analysis-tabs.tsx

## Out of scope
- real SQL generation
- real chart rendering
- semantic retrieval
- engine routing logic

## Acceptance Criteria
- model is asked for JSON
- backend parses structured output safely
- fallback works if parsing fails
- assumptions appear in UI
- app works on configured frontend port
```

---

## 11. Commit it

From repo root:

```bash
cd ~/workspace/dataprismai
git add .
git commit -m "feat: add structured GenBI response contract"
```

---

## What comes next

The next best step is the first real **GenBI execution layer** move:

* introduce a **semantic context service**
* replace hardcoded semantic context
* add a small local metric catalog
* map user questions to metrics/dimensions before prompting the LLM

That will be your first step from “chat app” to “actual governed GenBI system.”


=================================================

