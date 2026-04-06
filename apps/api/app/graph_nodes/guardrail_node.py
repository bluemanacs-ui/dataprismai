"""Guardrail node — rejects off-topic, greeting, or gibberish queries early."""
import re

_GREETINGS = {
    "hi", "hello", "hey", "helo", "hii", "hiii", "yo", "sup", "howdy",
    "good morning", "good afternoon", "good evening", "good night",
    "how are you", "how are u", "whats up", "what's up", "how do you do",
    "nice to meet you", "thanks", "thank you", "cheers", "bye", "goodbye",
    "ok", "okay", "yes", "no", "sure", "really", "cool", "great", "nice",
    "hello world", "test", "testing",
    # Identity phrases
    "who are you", "who are u", "what are you", "what are u",
    "who r u", "who r you", "what r u", "what r you",
    "where are you", "where are u", "where r you", "where r u",
    "what is your name", "what's your name", "whats ur name",
    "tell me about yourself", "introduce yourself",
    "are you a bot", "are you an ai", "are you real",
    # Complaints / meta
    "you give me nothing", "this is wrong", "that is wrong", "you are wrong",
    "not helpful", "useless", "stop it", "fix yourself",
}

_OFF_TOPIC_PATTERNS = [
    # Identity / capability questions about the bot itself
    r"^\s*(who|what)\s+(are|r)\s+(you|u|ur)\b",
    r"^\s*(what|who)\s+(is|r|are)\s+(your|ur)\s+name\b",
    r"^\s*(what|how)\s+(can|do)\s+(you|u)\s+(do|help|assist)\b",
    r"^\s*(tell\s+me\s+about\s+(your|ur)self|introduce\s+your|what\s+do\s+you\s+do)\b",
    r"^\s*(are\s+you|r\s+u)\s+(a\s+)?(bot|ai|robot|human|real|chatgpt|gpt)\b",
    # General off-topic
    r"^\s*(write|create|generate)\s+(a\s+)?(poem|story|song|essay|joke|code)\b",
    r"^\s*(who|what)\s+(is|are)\s+(god|jesus|allah|buddha|trump|biden|obama|elon|musk)\b",
    r"^\s*(what|how)\s+(is|to)\s+(cook|recipe|weather|temperature|stock price)\b",
    r"^\s*(tell\s+me\s+a\s+joke|make\s+me\s+laugh)\b",
    r"^\s*(i\s+love|i\s+hate|i\s+feel|i\s+am\s+sad|i\s+am\s+happy)\b",
    r"^\s*(play|watch|listen|movie|music|game|sport)\b",
]

_DATA_KEYWORDS = {
    "show", "list", "what", "how many", "top", "trend", "compare", "breakdown",
    "total", "count", "sum", "average", "avg", "rate", "fraud", "spend",
    "transaction", "transactions", "payment", "payments", "customer", "customers",
    "account", "accounts", "credit", "delinquency",
    "utilization", "dispute", "disputes", "merchant", "merchants", "category",
    "month", "year", "week", "date",
    "metric", "data", "report", "analysis", "analyze", "analyse", "query",
    "revenue", "volume", "distribution", "highest", "lowest", "most", "least",
    "which", "when", "chart", "graph", "table", "sql",
    "balance", "score", "income", "product", "segment", "region", "status",
    "by", "per", "between", "over", "last", "this", "recent", "current",
    "number", "percent", "percentage", "quartile", "median", "min", "max",
    # Domain-specific entities
    "card", "cards", "id", "ids", "statement", "statements",
    "alert", "alerts", "fraud_alert", "interchange", "fee",
    "limit", "balance", "available", "open", "closed", "active",
    "give", "get", "fetch", "find", "display", "pull",
}


def _is_gibberish(text: str) -> bool:
    """Heuristic: mostly consonant clusters or very short non-words."""
    if len(text) < 3:
        return True
    # If >70% consonants in a single token longer than 5 chars, likely gibberish
    words = text.split()
    for word in words:
        alpha = re.sub(r"[^a-z]", "", word.lower())
        if len(alpha) >= 6:
            vowels = sum(1 for c in alpha if c in "aeiou")
            if vowels / len(alpha) < 0.1:
                return True
    # Check if it's pure random chars with no real words
    real_words = sum(1 for w in words if len(re.sub(r"[^a-z]", "", w.lower())) >= 3)
    if len(words) >= 2 and real_words == 0:
        return True
    return False


def _classify(message: str) -> str:
    """Return 'valid', 'clarify', 'greeting', 'gibberish', or 'off_topic'."""
    stripped = message.strip().lower()

    if not stripped:
        return "gibberish"

    # Check greeting set
    if stripped in _GREETINGS or any(stripped.startswith(g + " ") or stripped.endswith(" " + g) for g in _GREETINGS):
        return "greeting"

    # Check off-topic patterns
    for pat in _OFF_TOPIC_PATTERNS:
        if re.search(pat, stripped, re.IGNORECASE):
            return "off_topic"

    # Check gibberish
    if _is_gibberish(stripped):
        return "gibberish"

    # Check pronoun-only follow-up with no entity — needs clarification
    if _is_pronoun_followup(message):
        return "clarify"

    # Check if message contains at least one data keyword
    words_in_msg = set(re.findall(r"\b\w+\b", stripped))
    if words_in_msg & _DATA_KEYWORDS:
        return "valid"

    # No data keyword found — not a data query regardless of length
    return "off_topic"


# Patterns that indicate a pronoun-only follow-up (no entity anchor)
_PRONOUN_FOLLOW_UP = re.compile(
    r"^\s*(?:what\s+is|what's|show\s+me|give\s+me|get|find|display|tell\s+me)?"
    r"\s*(?:his|her|their|its|this person'?s?|that person'?s?|he|she|they)\s+"
    r"(?:phone|number|email|address|name|id|account|card|balance|score|limit|details?|info)",
    re.IGNORECASE,
)

_CONTEXT_PRONOUNS = re.compile(
    r"\b(his|her|their|its|he|she|they|this one|that one|the same|above|those|them)\b",
    re.IGNORECASE,
)

# An entity anchor means the message also has an ID, name or explicit noun
_ENTITY_ANCHOR = re.compile(
    r"(?:customer|merchant|card|account|transaction|payment)\s*(?:id|#|number|named?|called?)\s*\S+"
    r"|\bCUST_\d+\b|\bMERCH_\d+\b|\bCARD_\d+\b|\bACC_\d+\b",
    re.IGNORECASE,
)


def _is_pronoun_followup(text: str) -> bool:
    """Returns True when the message uses a pronoun reference with no entity anchor."""
    if _PRONOUN_FOLLOW_UP.search(text):
        return True
    # Broader: has a context pronoun but no entity anchor and is short
    if _CONTEXT_PRONOUNS.search(text) and not _ENTITY_ANCHOR.search(text) and len(text.split()) <= 10:
        return True
    return False



_GUARDRAIL_RESPONSES = {
    "greeting": (
        "👋 Hello! I'm **DataPrismAI**, your AI-powered financial analytics assistant. "
        "I analyze credit card, payment, fraud, and risk data to surface actionable insights.\n\n"
        "Try asking:\n"
        "- *Show total spend by merchant category*\n"
        "- *What is the fraud rate by merchant?*\n"
        "- *Show delinquency rate breakdown*"
    ),
    "gibberish": (
        "I couldn't understand that query. Please ask a question about your financial data.\n\n"
        "**Examples:**\n"
        "- *Show total spend by month*\n"
        "- *List customers with highest number of cards*\n"
        "- *What is the payment volume trend?*"
    ),
    "off_topic": (
        "I'm **DataPrismAI** — a financial data analytics assistant specializing in credit card, "
        "payment, fraud, and risk analytics. I'm not able to help with that request.\n\n"
        "**Try one of these instead:**\n"
        "- *Show fraud rate by merchant category*\n"
        "- *What is the total spend this year?*\n"
        "- *Show account delinquency by status*"
    ),
    "clarify": (
        "I need a bit more context. It looks like you're referring to a specific record from a previous result — "
        "please include the identifier or name so I can look it up.\n\n"
        "**For example:**\n"
        "- *What is the phone number for customer CUST_000023?*\n"
        "- *Show all cards for account ACC_000105*\n"
        "- *Show transactions for customer CUST_000174*"
    ),
}


def guardrail_node(state: dict) -> dict:
    message = state.get("user_message", "")
    thread_id = state.get("thread_id", "")
    classification = _classify(message)

    # Pronoun follow-up (e.g. "what is his address") is only ambiguous when there's
    # no prior thread context. If the thread has history the entity_resolver can handle it.
    if classification == "clarify" and thread_id:
        from app.services.thread_memory import get_context, get_last_entity  # avoid circular at top-level
        if get_context(thread_id) or get_last_entity(thread_id):
            classification = "valid"

    if classification != "valid":
        response_text = _GUARDRAIL_RESPONSES[classification]
        follow_ups = {
            "greeting": ["Show total spend by merchant category", "What is the fraud rate?", "Show payment volume by month"],
            "gibberish": ["Show total spend by month", "List customers with most cards", "What is the fraud rate?"],
            "off_topic": ["Show fraud rate by merchant category", "What is total spend this year?", "Show account delinquency by status"],
            "clarify": ["Show details for customer CUST_000001", "List all cards for account ACC_000001", "Show transactions by customer"],
        }.get(classification, [])
        return {
            **state,
            "guardrail_blocked": True,
            "answer": response_text,
            "insights": [],
            "follow_ups": follow_ups,
            "reasoning_steps": [f"Guardrail: query classified as '{classification}' — returning canned response."],
        }

    return {
        **state,
        "guardrail_blocked": False,
        "reasoning_steps": [f"Guardrail: query classified as 'valid' — proceeding with data pipeline."],
    }
