import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s()]{8,}\d)")
NAME_PATTERNS = [
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z '\-]{1,30})", re.IGNORECASE),
    re.compile(r"\bi am\s+([A-Za-z][A-Za-z '\-]{1,30})", re.IGNORECASE),
    re.compile(r"\bi'm\s+([A-Za-z][A-Za-z '\-]{1,30})", re.IGNORECASE),
]


def _text(message):
    return str(message or "").strip().lower()


def create_profile():
    """Create a lightweight session profile for personalized conversation."""
    return {
        "name": "",
        "goal": "",
        "target_customer": "",
        "problem": "",
        "budget": "",
        "timeline": "",
    }


def _clean_value(value):
    return str(value or "").strip(" .,!?:;")


def _extract_name(message):
    raw_text = str(message or "").strip()
    for pattern in NAME_PATTERNS:
        match = pattern.search(raw_text)
        if not match:
            continue
        candidate = _clean_value(match.group(1))
        words = [w for w in candidate.split() if w]
        if len(words) > 3:
            candidate = " ".join(words[:3])
        first_word = candidate.split(" ", 1)[0].lower()
        blocked = {"building", "creating", "launching", "working", "trying", "planning", "developing"}
        if first_word in blocked:
            continue
        return candidate.title()
    return ""


def _extract_goal(message):
    text = str(message or "")
    patterns = [
        re.compile(r"\b(?:i want to|we want to|my goal is|i need to)\s+([^.!?\n]+)", re.IGNORECASE),
        re.compile(r"\b(?:looking to|trying to)\s+([^.!?\n]+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group(1))
            lower_value = value.lower()
            cut_markers = (" and my budget", " budget is", " with budget", " and budget")
            for marker in cut_markers:
                idx = lower_value.find(marker)
                if idx > 0:
                    value = value[:idx].strip()
                    break
            return value
    return ""


def _extract_target_customer(message):
    text = str(message or "")
    patterns = [
        re.compile(r"\b(?:target users?|target customers?)\s*(?:are|is|:)?\s*([^.!?\n]+)", re.IGNORECASE),
        re.compile(r"\b(?:for)\s+([^.!?\n]{3,60})", re.IGNORECASE),
        re.compile(r"\bhelp\s+([^.!?\n]{3,40}?)\s+(?:reduce|increase|improve|with|by)\b", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group(1))
            if value and len(value.split()) <= 12:
                return value
    return ""


def _extract_problem(message):
    text = str(message or "")
    patterns = [
        re.compile(r"\b(?:problem|pain|challenge|issue)\s*(?:is|:)?\s*([^.!?\n]+)", re.IGNORECASE),
        re.compile(r"\bstruggling with\s+([^.!?\n]+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return _clean_value(match.group(1))
    return ""


def _extract_budget(message):
    text = str(message or "")
    patterns = [
        re.compile(r"(\$\s?\d[\d,]*(?:\s*(?:usd|dollars))?)", re.IGNORECASE),
        re.compile(r"(\d[\d,]*\s*(?:inr|usd|dollars))", re.IGNORECASE),
        re.compile(r"\b(?:budget)\s*(?:is|:)?\s*([^\n.!?]+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = _clean_value(match.group(1))
            timeline_words = ("day", "days", "week", "weeks", "month", "months", "asap", "soon")
            if any(word in value.lower() for word in timeline_words) and not any(ch.isdigit() for ch in value):
                continue
            return value
    return ""


def _extract_timeline(message):
    text = str(message or "")
    patterns = [
        re.compile(r"\b(?:timeline)\s*(?:is|:)?\s*([^.!?\n]+)", re.IGNORECASE),
        re.compile(r"\b(?:in|within|by)\s+(\d+\s*(?:day|days|week|weeks|month|months))\b", re.IGNORECASE),
        re.compile(r"\b(asap|soon|this month|next month)\b", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return _clean_value(match.group(1))
    return ""


def update_profile(profile, message):
    """Update profile with any details found in latest user message."""
    current = dict(profile or create_profile())

    name = _extract_name(message)
    goal = _extract_goal(message)
    target_customer = _extract_target_customer(message)
    problem = _extract_problem(message)
    budget = _extract_budget(message)
    timeline = _extract_timeline(message)

    if name:
        current["name"] = name
    if goal:
        current["goal"] = goal
    if target_customer:
        current["target_customer"] = target_customer
    if problem:
        current["problem"] = problem
    if budget:
        current["budget"] = budget
    if timeline:
        current["timeline"] = timeline

    return current


def detect_stage(message):
    """Detect current lead stage from user intent signals."""
    text = _text(message)

    if EMAIL_RE.search(text) or PHONE_RE.search(text):
        return "contact_shared"

    decision_keywords = ("price", "cost", "package", "plan", "book", "demo", "call")
    if any(word in text for word in decision_keywords):
        return "decision"

    qualification_keywords = ("budget", "timeline", "month", "week", "team", "mvp", "launch")
    if any(word in text for word in qualification_keywords):
        return "qualification"

    uncertain_keywords = ("not sure", "confused", "don't know", "stuck", "unclear")
    if any(word in text for word in uncertain_keywords):
        return "uncertain"

    discovery_keywords = ("idea", "problem", "customer", "users", "startup", "business", "app")
    if any(word in text for word in discovery_keywords):
        return "discovery"

    return "general"


def _personalization_brief(profile, history):
    parts = []
    if profile.get("name"):
        parts.append(f"Use the user's name naturally: {profile['name']}.")

    known = []
    if profile.get("goal"):
        known.append(f"goal={profile['goal']}")
    if profile.get("target_customer"):
        known.append(f"target_customer={profile['target_customer']}")
    if profile.get("problem"):
        known.append(f"problem={profile['problem']}")
    if profile.get("budget"):
        known.append(f"budget={profile['budget']}")
    if profile.get("timeline"):
        known.append(f"timeline={profile['timeline']}")
    if known:
        parts.append("Known user context: " + "; ".join(known) + ".")

    if history:
        recent = " | ".join(history[-3:])
        parts.append(f"Recent user messages: {recent}")

    parts.append("Avoid generic filler. Mirror the user's wording and keep it practical.")
    return " ".join(parts)


def add_guidance(stage, message, profile=None, history=None):
    """Return tactical + personalization guidance for lead-focused responses."""
    text = _text(message)
    has_audience = bool(profile and profile.get("target_customer")) or any(
        word in text for word in ("customer", "users", "students", "founders", "smb", "businesses")
    )
    has_problem = bool(profile and profile.get("problem")) or any(
        word in text for word in ("problem", "pain", "issue", "struggle")
    )
    has_budget = bool(profile and profile.get("budget")) or any(
        word in text for word in ("budget", "cost", "price", "$", "usd", "inr")
    )
    has_timeline = bool(profile and profile.get("timeline")) or any(
        word in text for word in ("week", "month", "timeline", "asap", "soon", "launch")
    )

    stage_guidance = {
        "discovery": "Acknowledge their idea and ask one precise question about target user or core pain.",
        "uncertain": "Reduce pressure, give one practical validation step, and ask one simple next-step question.",
        "qualification": "Ask one focused qualification question about budget, timeline, or decision-maker.",
        "decision": "Give concise offer framing and invite them to take the next step today.",
        "contact_shared": "Thank them for sharing contact details and confirm follow-up action clearly.",
        "general": "Briefly clarify their goal and ask one question that uncovers business pain.",
    }

    missing_fields = []
    if not has_audience:
        missing_fields.append("target customer")
    if not has_problem:
        missing_fields.append("core problem")
    if not has_budget:
        missing_fields.append("budget range")
    if not has_timeline:
        missing_fields.append("timeline")

    parts = [stage_guidance.get(stage, stage_guidance["general"])]
    if missing_fields:
        parts.append("Missing qualification fields: " + ", ".join(missing_fields) + ".")

    parts.append(_personalization_brief(profile or {}, history or []))
    parts.append("Keep response short (2-4 sentences), useful, and include only one question.")
    return " ".join(parts)
