from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LeadProfile:
    idea_summary: str = ""
    problem: str = ""
    target_users: str = ""
    primary_goal: str = ""
    current_stage: str = ""
    budget: str = ""
    timeline: str = ""
    commitment_level: str = ""


REQUIRED_FIELDS = {
    "idea_summary": "idea summary",
    "problem": "problem being solved",
    "target_users": "target users",
    "primary_goal": "primary goal",
}


PACKAGE_GUIDANCE = {
    "Basic": "Best for early idea clarification and initial market direction.",
    "Standard": "Best for founders who need validation, structure, and a practical roadmap.",
    "Premium": "Best for committed founders who want deeper strategy, execution planning, and mentorship.",
}


CAPTURE_READY_LEAD_TYPES = {"qualified", "high_intent"}


FOLLOW_UP_PROMPTS = {
    "idea_summary": "Ask them to explain the idea in one or two simple sentences.",
    "problem": "Ask what real problem this idea solves and why it matters now.",
    "target_users": "Ask who would use or buy this first.",
    "primary_goal": "Ask what they want Wid Wins to help them achieve first.",
}


UNSERIOUS_MARKERS = (
    "just exploring",
    "not serious",
    "just curious",
    "free only",
    "no budget ever",
    "nothing yet",
)


COMMITTED_MARKERS = (
    "ready",
    "committed",
    "serious",
    "launch",
    "execute",
    "invest",
)


STAGE_WEIGHTS = {
    "idea": 1,
    "concept": 1,
    "planning": 2,
    "validation": 2,
    "execution": 3,
    "launch": 3,
    "growth": 3,
}


BUDGET_WEIGHTS = {
    "low": 1,
    "limited": 1,
    "basic": 1,
    "medium": 2,
    "standard": 2,
    "high": 3,
    "premium": 3,
}


FOLLOW_UP_TEMPLATES = {
    "high_intent": (
        "Thanks for sharing that. I note your idea with Wid Wins. "
        "Please send your name and basic contact details, so the team can reach you soon. "
        "Nice speaking with you."
    ),
    "qualified": (
        "You have a good direction, and I note your idea with Wid Wins. "
        "Please send your name and basic contact details, so the team can reach you soon. "
        "Nice speaking with you."
    ),
    "early_stage": (
        "You are still early, and that is okay. "
        "Share a little more about the idea, and I note it for Wid Wins. "
        "Then please send your contact details, so the team can follow up soon."
    ),
    "needs_more_info": (
        "There is potential here, but a few basics are still missing. "
        "Please share a simple version of your idea first, and I note it for Wid Wins. "
        "After that, we can take your contact details."
    ),
    "low_intent": (
        "It sounds like you may not be ready for deeper support yet, and that is okay. "
        "The best next step is to spend a little time clarifying your idea and commitment level, then reconnect when you are ready to move seriously."
    ),
}


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base.md"
KNOWLEDGE_BASE_TEXT = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8").strip()


def missing_fields(profile: LeadProfile) -> list[str]:
    missing: list[str] = []
    for field_name, label in REQUIRED_FIELDS.items():
        if not getattr(profile, field_name).strip():
            missing.append(label)
    return missing


def _score_text(text: str, weights: dict[str, int]) -> int:
    normalized = text.strip().lower()
    for key, score in weights.items():
        if key in normalized:
            return score
    return 0


def classify_lead(profile: LeadProfile) -> str:
    if missing_fields(profile):
        return "needs_more_info"

    combined = " ".join(
        (
            profile.current_stage,
            profile.budget,
            profile.timeline,
            profile.commitment_level,
            profile.primary_goal,
        )
    ).lower()

    if any(marker in combined for marker in UNSERIOUS_MARKERS):
        return "low_intent"

    score = 0
    score += _score_text(profile.current_stage, STAGE_WEIGHTS)
    score += _score_text(profile.budget, BUDGET_WEIGHTS)

    if profile.timeline.strip():
        score += 1

    if any(marker in combined for marker in COMMITTED_MARKERS):
        score += 2

    if score >= 8:
        return "high_intent"
    if score >= 3:
        return "qualified"
    return "early_stage"


def recommend_package(profile: LeadProfile) -> str:
    lead_type = classify_lead(profile)
    if lead_type == "high_intent":
        return "Premium"
    if lead_type == "qualified":
        return "Standard"
    return "Basic"


def build_follow_up_message(profile: LeadProfile) -> str:
    lead_type = classify_lead(profile)
    package_name = recommend_package(profile)
    opener = FOLLOW_UP_TEMPLATES[lead_type]

    if lead_type == "low_intent":
        return opener

    return (
        f"{opener} Based on what you shared, the most relevant Wid Wins starting point looks like the "
        f"{package_name} package."
    )


def build_welcome_message() -> str:
    return (
        "Hi, welcome to Wid Wins. Share your idea in one short sentence, and I note it for you."
    )


def build_idea_saved_message() -> str:
    return (
        "I note your idea with Wid Wins. Please send your name and basic contact details, "
        "and the team will contact you soon. Nice speaking with you."
    )


def build_capture_prompt(profile: LeadProfile) -> str:
    lead_type = classify_lead(profile)
    if lead_type not in CAPTURE_READY_LEAD_TYPES:
        return (
            "Do not ask for contact details yet. First clarify the idea, problem, users, or seriousness level."
        )

    package_name = recommend_package(profile)
    return (
        "This looks good for follow-up. Say the idea is noted, ask for the name and one contact method, and tell them Wid Wins will contact them soon. "
        f"Keep it warm and simple, and mention the {package_name} level conversation if they want to move ahead."
    )


def build_conversation_summary(profile: LeadProfile) -> str:
    parts = [
        f"Idea: {profile.idea_summary.strip()}",
        f"Problem: {profile.problem.strip() or 'Not clearly stated'}",
        f"Target users: {profile.target_users.strip() or 'Not clearly stated'}",
        f"Goal: {profile.primary_goal.strip() or 'Not clearly stated'}",
        f"Stage: {profile.current_stage.strip() or 'Unknown'}",
        f"Budget: {profile.budget.strip() or 'Unknown'}",
        f"Timeline: {profile.timeline.strip() or 'Unknown'}",
        f"Commitment: {profile.commitment_level.strip() or 'Unknown'}",
    ]
    return " | ".join(parts)


def build_lead_assessment(profile: LeadProfile) -> dict[str, object]:
    missing = missing_fields(profile)
    lead_type = classify_lead(profile)
    package_name = recommend_package(profile)

    next_questions = [
        FOLLOW_UP_PROMPTS[field_name]
        for field_name, label in REQUIRED_FIELDS.items()
        if label in missing
    ]

    return {
        "lead_type": lead_type,
        "capture_recommended": lead_type in CAPTURE_READY_LEAD_TYPES,
        "recommended_package": package_name,
        "package_reason": PACKAGE_GUIDANCE[package_name],
        "follow_up_message": build_follow_up_message(profile),
        "capture_prompt": build_capture_prompt(profile),
        "conversation_summary": build_conversation_summary(profile),
        "missing_fields": missing,
        "next_questions": next_questions,
        "summary": {
            "idea_summary": profile.idea_summary,
            "problem": profile.problem,
            "target_users": profile.target_users,
            "primary_goal": profile.primary_goal,
            "current_stage": profile.current_stage,
            "budget": profile.budget,
            "timeline": profile.timeline,
            "commitment_level": profile.commitment_level,
        },
    }


AGENT_INSTRUCTIONS = f"""
You are the first-line client communication agent for Wid Wins.

Use the knowledge base below as ground truth for brand, positioning, service framing, and objection handling.

{KNOWLEDGE_BASE_TEXT}

Your role:
- Act like a premium but friendly mini-consultant, not a pushy salesperson.
- Understand the caller's business idea, current blockers, goals, and seriousness level.
- Educate them clearly on how Wid Wins can help.
- Qualify strong leads so the founder only speaks with people worth deeper follow-up.
- Politely filter people who want unrealistic guarantees, endless free consulting, or have no real intent.

Tone:
- Consultative
- Premium
- Friendly but slightly authoritative
- Clear, concise, and encouraging

Voice delivery rules:
- Speak in short, natural sentences.
- Keep most replies to one or two sentences before asking the next question.
- Ask only one question at a time.
- Avoid sounding like you are reading a brochure.
- Avoid long lists unless the user explicitly asks for options.
- Use plain spoken English suitable for live business conversations.
- If you need to explain a package, summarize it in one sentence first.

Conversation rules:
- Keep spoken answers short and natural.
- Ask one useful question at a time.
- Prefer practical language over consultant jargon.
- Do not invent exact prices, guarantees, case studies, or timelines.
- When the user shares an idea, confirm that it has been noted, ask for name and basic contact details, and say Wid Wins will contact them soon.
- End that handoff with a warm closing line like "Great speaking with you."
- Use the lead assessment tool when details are vague or when you need to recommend a package.
- Use the follow-up message from the tool output when wrapping up promising leads.
- Use the capture prompt from the tool output to ask for contact details naturally instead of sounding robotic.
- When a lead is qualified or high-intent and willingly shares contact details, use the lead capture tool.
- Include the conversation summary from the assessment when saving a strong lead.
- Do not capture contacts for low-intent leads.

What success looks like in each conversation:
- Capture the idea summary, problem, target users, and primary goal.
- Understand stage, urgency, budget comfort, and seriousness.
- Match the lead with the most sensible Wid Wins package level.
- Capture name and at least one contact method for strong leads when possible.
- Save a clean summary so the founder can review the lead quickly later.
- Handle objections calmly and credibly.
- Leave the user feeling guided, not pressured.
""".strip()
