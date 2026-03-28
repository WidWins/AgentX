from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any

from livekit.agents import llm
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, APIConnectOptions, NotGivenOr
from wid_wins_agent import LeadProfile, build_lead_assessment


_INTRO_NAME_RE = re.compile(
    r"^\s*(?:hi|hello|hey)?[\s,!.]*"
    r"(?:i am|i'm|im|my name is)\s+([a-zA-Z][a-zA-Z '\-]{0,30})\s*$",
    re.IGNORECASE,
)

_BUSINESS_HINTS = (
    "build",
    "building",
    "startup",
    "business",
    "school",
    "app",
    "platform",
    "product",
    "agency",
    "service",
    "company",
)

_PROBLEM_HINTS = (
    "problem",
    "pain",
    "struggle",
    "issue",
    "challenge",
    "manual",
    "waste",
)

_GOAL_HINTS = (
    "goal",
    "want to",
    "need to",
    "aim to",
    "looking to",
    "plan to",
)

_TIMELINE_HINTS = (
    "week",
    "month",
    "quarter",
    "year",
    "asap",
    "soon",
    "deadline",
)

_COMMITMENT_HINTS = (
    "serious",
    "committed",
    "ready",
    "invest",
    "launch",
    "execute",
)

_BUDGET_HINTS = (
    "budget",
    "premium",
    "standard",
    "basic",
    "low",
    "high",
)

_STAGE_HINTS = ("idea", "planning", "validation", "execution", "launch", "growth")


def _latest_user_text(chat_ctx: llm.ChatContext) -> str:
    for message in reversed(chat_ctx.messages()):
        if message.role == "user":
            return (message.text_content or "").strip()
    return ""


def _extract_name_from_intro(text: str) -> str:
    match = _INTRO_NAME_RE.match(text.strip())
    if not match:
        return ""
    name = re.sub(r"\s+", " ", match.group(1).strip()).strip(" .,!?:;")
    lower_name = name.lower()

    # Avoid false positives like "im building business school"
    if any(token in lower_name for token in _BUSINESS_HINTS):
        return ""

    parts = name.split()
    if len(parts) > 3:
        return ""

    return name.title()


def _next_question_for_text(user_text: str) -> str:
    lowered = user_text.lower()
    if any(token in lowered for token in ("for ", "target", "customer", "users", "audience")):
        return "What is the main result you want in the next 30 days?"
    if any(token in lowered for token in ("app", "agent", "startup", "platform", "service", "product", "business", "idea")):
        return "Who is your first target user?"
    return "What problem are you trying to solve?"


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def _user_messages(chat_ctx: llm.ChatContext) -> list[str]:
    return [
        (message.text_content or "").strip()
        for message in chat_ctx.messages()
        if message.role == "user" and (message.text_content or "").strip()
    ]


def _extract_target_users(text: str) -> str:
    patterns = (
        r"(?:target users?|customers?|audience)\s*(?:are|is|:)?\s+(.+)",
        r"\bfor\s+([a-zA-Z0-9][a-zA-Z0-9 ,&'/-]{2,80})$",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .,!?:;")
    return ""


def _extract_lead_profile(chat_ctx: llm.ChatContext) -> LeadProfile:
    profile = LeadProfile()
    user_messages = _user_messages(chat_ctx)

    for text in user_messages:
        lowered = text.lower()
        intro_name = _extract_name_from_intro(text)

        if not profile.idea_summary and not intro_name:
            if _contains_any(lowered, _BUSINESS_HINTS) or len(text.split()) >= 6:
                profile.idea_summary = text

        if not profile.problem and _contains_any(lowered, _PROBLEM_HINTS):
            profile.problem = text

        if not profile.target_users:
            target_users = _extract_target_users(text)
            if target_users:
                profile.target_users = target_users

        if not profile.primary_goal and _contains_any(lowered, _GOAL_HINTS):
            profile.primary_goal = text

        if not profile.timeline and _contains_any(lowered, _TIMELINE_HINTS):
            profile.timeline = text

        if not profile.commitment_level and _contains_any(lowered, _COMMITMENT_HINTS):
            profile.commitment_level = text

        if not profile.budget and _contains_any(lowered, _BUDGET_HINTS):
            profile.budget = text

        if not profile.current_stage:
            for stage in _STAGE_HINTS:
                if stage in lowered:
                    profile.current_stage = stage
                    break

    if not profile.idea_summary:
        for text in reversed(user_messages):
            if not _extract_name_from_intro(text) and len(text.split()) >= 4:
                profile.idea_summary = text
                break

    return profile


def _question_for_missing_field(field_label: str, latest_user_text: str) -> str:
    field = field_label.lower()
    if "problem" in field:
        return "What specific pain are they facing today without your solution?"
    if "target users" in field:
        return "Who exactly is your first target user segment?"
    if "primary goal" in field:
        return "What is your main goal for the next 30 days?"
    if "idea summary" in field:
        return _next_question_for_text(latest_user_text)
    return _next_question_for_text(latest_user_text)


def _build_local_reply(chat_ctx: llm.ChatContext) -> str:
    user_text = _latest_user_text(chat_ctx)
    if not user_text:
        return (
            "Local mode is active and ready. "
            "Tell me your idea in one sentence, and I will help you qualify it for Wid Wins."
        )

    name = _extract_name_from_intro(user_text)
    profile = _extract_lead_profile(chat_ctx)
    assessment = build_lead_assessment(profile)
    missing_fields = [str(field) for field in assessment.get("missing_fields", [])]

    if name and not profile.idea_summary:
        return (
            f"Nice to meet you, {name}. "
            "Local mode is active without cloud inference credits, and I can still run a full qualification flow. "
            "Tell me your idea in one line and who it is for."
        )

    if missing_fields:
        context_bits: list[str] = []
        if profile.idea_summary:
            context_bits.append(f"Idea: {profile.idea_summary}")
        if profile.target_users:
            context_bits.append(f"Target users: {profile.target_users}")

        summary = ""
        if context_bits:
            summary = f"I noted {', '.join(context_bits[:2])}. "
        else:
            summary = f"I heard: '{user_text}'. "

        next_question = _question_for_missing_field(missing_fields[0], user_text)
        return (
            f"{summary}"
            "Local mode is active without cloud inference credits, and I can still guide this conversation step by step. "
            f"{next_question}"
        )

    lead_type = str(assessment.get("lead_type", "qualified")).replace("_", " ")
    recommended_package = str(assessment.get("recommended_package", "Standard"))
    return (
        "Great clarity. "
        f"Based on what you shared, this looks like a {lead_type} lead, and {recommended_package} is the best starting package. "
        "Would you like a 60-second action plan or a follow-up message draft next?"
    )


class _LocalStubLLMStream(llm.LLMStream):
    def __init__(
        self,
        llm_v: llm.LLM,
        *,
        response_text: str,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(llm_v, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._response_text = response_text

    async def _run(self) -> None:
        chunk_id = f"local_{uuid.uuid4().hex[:12]}"
        # Simulate word-by-word streaming for better TTS testing
        words = self._response_text.split(" ")
        for i, word in enumerate(words):
            content = word + (" " if i < len(words) - 1 else "")
            delta = llm.ChoiceDelta(
                role="assistant" if i == 0 else None,
                content=content,
            )
            await self._event_ch.send(llm.ChatChunk(id=chunk_id, delta=delta))
            await asyncio.sleep(0)  # Zero delay for maximum performance simulation

        self._event_ch.close()


class LocalStubLLM(llm.LLM):
    @property
    def model(self) -> str:
        return "wid-wins-local-stub"

    @property
    def provider(self) -> str:
        return "local"

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[llm.ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> llm.LLMStream:
        del parallel_tool_calls, tool_choice, extra_kwargs
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        return _LocalStubLLMStream(
            self,
            response_text=_build_local_reply(chat_ctx),
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )

    async def aclose(self) -> None:
        return None
