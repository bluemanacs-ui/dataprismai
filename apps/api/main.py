from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.semantic import router as semantic_router
from app.api.skills import router as skills_router

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
app.include_router(semantic_router)
app.include_router(skills_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "DataPrismAI API"}
