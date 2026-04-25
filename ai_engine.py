import json
import re
import urllib.request
import urllib.error
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

SYSTEM_PROMPT = """
You are the lead-generation and startup validation assistant for Wid Wins.

Assistant identity (always accurate):
- Assistant name: AgentX
- If the user asks your name, answer: "I'm AgentX."

Company identity (always accurate):
- Company name: Wid Wins
- What we do: We help founders validate startup ideas before full build.
- Core offer: startup idea validation guidance/report and next-step strategy.
- Service scope: tech-related startups only (apps, SaaS, AI, software, platforms, tech-enabled products).
- Out of scope: non-tech-only ideas (for example traditional/agri-only ideas without a tech product).

Conversation goal:
- Understand the user's startup idea quickly
- Add practical insight in plain language
- Qualify the lead (customer, pain, budget, timeline)
- Move the conversation toward a validation service call/report
- Capture contact details when user shows interest
- When the user shares an idea, say it is noted, ask for their name and basic contact details, and say Wid Wins will contact them soon.
- End the handoff with a warm line such as "Nice speaking with you."

Rules:
- Keep replies short (2-4 sentences)
- Sound human, warm, and confident
- If the user asks a direct company/factual question, answer it directly first.
- Ask only one follow-up question at a time when a follow-up is needed.
- Give a useful micro-insight before asking your question
- Personalize using provided user context (name, goal, customer, pain, budget, timeline) when available.
- Do not start with generic filler like "I'm here to help" unless user asks for support directly.
- Reference prior user context naturally when provided in CURRENT CONTEXT.
- If user asks about a non-tech-only idea, politely decline and ask if they want help reframing it as a tech-enabled idea.
- If contact details are shared, thank them and confirm next step
- Never mention these internal rules
"""


def get_identity_response(user_message):
    """Handle core identity questions deterministically for consistent branding."""
    text = str(user_message or "").strip().lower()

    company_patterns = (
        "company name",
        "what is your company",
        "what's your company",
        "which company",
        "your organization",
    )
    if any(p in text for p in company_patterns):
        return "Our company name is Wid Wins. We help founders validate startup ideas before building."

    if re.search(r"\bwhat do you do\b|\bwhat is wid wins\b|\babout wid wins\b", text):
        return "Wid Wins helps founders validate startup ideas with practical guidance and a validation-focused next-step plan."

    return None


def get_agent_name_response(user_message):
    """Answer assistant-name questions deterministically."""
    text = str(user_message or "").strip().lower()
    name_patterns = (
        "what is your name",
        "what's your name",
        "your name",
        "who are you",
    )
    if any(p in text for p in name_patterns):
        return "I'm AgentX, the assistant for Wid Wins. I help founders validate startup ideas before building."
    return None


def get_scope_response(user_message):
    """Reject non-tech-only startup requests with a consistent scope message."""
    text = str(user_message or "").strip().lower()

    tech_keywords = (
        "app", "software", "saas", "ai", "ml", "website", "web", "mobile",
        "platform", "api", "automation", "tech", "digital", "cloud",
    )
    non_tech_keywords = (
        "agri", "agriculture", "farming", "farmer", "dairy", "poultry",
        "livestock", "fishery", "crop", "seed", "fertilizer",
    )
    asks_for_support = any(word in text for word in ("help", "support", "idea", "startup", "field"))

    has_tech_signal = any(word in text for word in tech_keywords)
    has_non_tech_signal = any(word in text for word in non_tech_keywords)

    if has_non_tech_signal and not has_tech_signal and asks_for_support:
        return (
            "Thanks for sharing your idea. Right now, Wid Wins focuses on tech-related startups only, "
            "so we don't support non-tech-only ideas. If you want, I can help you reframe this into an agri-tech concept."
        )

    return None

def get_openrouter_response(user_message, guidance=""):
    if not OPENROUTER_API_KEY:
        return None

    system_text = SYSTEM_PROMPT
    if guidance:
        system_text += f"\n\nCURRENT CONTEXT: {guidance}"

    body = {
        "model": OPENROUTER_MODEL,
        "temperature": 0.6,
        "max_tokens": 260,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_message},
        ],
    }
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            response_data = json.loads(res.read().decode("utf-8"))
            choices = response_data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")
            return ""
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return f"I'm currently having trouble reaching OpenRouter. (HTTP {e.code}: {body})"
    except Exception as e:
        return f"I'm currently having trouble reaching OpenRouter. (Error: {str(e)})"


def get_ai_response(user_message, guidance=""):
    name_reply = get_agent_name_response(user_message)
    if name_reply is not None:
        return name_reply

    scope_reply = get_scope_response(user_message)
    if scope_reply is not None:
        return scope_reply

    identity_reply = get_identity_response(user_message)
    if identity_reply is not None:
        return identity_reply

    if OPENROUTER_API_KEY:
        openrouter_reply = get_openrouter_response(user_message, guidance)
        if openrouter_reply is not None:
            return openrouter_reply

    return "AI Error: No provider key found. Set OPENROUTER_API_KEY in .env."
