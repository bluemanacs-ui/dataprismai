from app.prompts.persona_loader import load_persona_prompt as load_persona

def persona_node(state: dict) -> dict:
    persona = state.get("persona", "analyst")
    try:
        persona_text = load_persona(persona)
    except Exception:
        persona_text = ""
    return {**state, "persona": persona, "_persona_text": persona_text}
