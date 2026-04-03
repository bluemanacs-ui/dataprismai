from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "personas"


def load_persona_prompt(persona: str) -> str:
    safe_persona = (persona or "analyst").strip().lower()
    file_path = BASE_DIR / f"{safe_persona}.txt"

    if not file_path.exists():
        file_path = BASE_DIR / "analyst.txt"

    return file_path.read_text(encoding="utf-8")
