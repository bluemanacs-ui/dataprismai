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
