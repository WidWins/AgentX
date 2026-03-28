from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
)
from livekit.plugins import silero
from pathlib import Path
import os
import socket
import sys
from env_loader import load_first_env_file
from lead_store import save_lead
from local_stub_llm import LocalStubLLM
from runtime_utils import configure_utf8_stdio
from stt_config import DEEPGRAM_BACKEND, INFERENCE_BACKEND, resolve_stt_settings
from wid_wins_agent import AGENT_INSTRUCTIONS, LeadProfile, build_lead_assessment

try:
    from livekit.plugins import deepgram
except ImportError:
    deepgram = None

try:
    from livekit.plugins import noise_cancellation
except ImportError:
    noise_cancellation = None

BASE_DIR = Path(__file__).resolve().parent
load_first_env_file((BASE_DIR / ".env", BASE_DIR / "tests/.env"))

# Single fixed ElevenLabs voice through LiveKit Inference.
TTS_MODEL = "elevenlabs/eleven_flash_v2_5"
TTS_VOICE = "Xb7hH8MSUJpSbSDYk0k2"
TTS_LANGUAGE = os.getenv("WID_WINS_TTS_LANGUAGE", "en")
TTS_SPEED = float(os.getenv("WID_WINS_TTS_SPEED", "1.0"))
_STT_SETTINGS = resolve_stt_settings()
STT_BACKEND = _STT_SETTINGS["backend"]
STT_LANGUAGE = _STT_SETTINGS["language"]
STT_MODEL = _STT_SETTINGS["inference_model"]
STT_PLUGIN_MODEL = _STT_SETTINGS["plugin_model"]
TURN_DETECTION = os.getenv("WID_WINS_TURN_DETECTION", "vad")
MIN_ENDPOINTING_DELAY = float(os.getenv("WID_WINS_MIN_ENDPOINTING_DELAY", "0.4"))
MIN_INTERRUPTION_DURATION = float(os.getenv("WID_WINS_MIN_INTERRUPTION_DURATION", "1.0"))
FALSE_INTERRUPTION_TIMEOUT = float(os.getenv("WID_WINS_FALSE_INTERRUPTION_TIMEOUT", "2.0"))
AEC_WARMUP_DURATION = float(os.getenv("WID_WINS_AEC_WARMUP_DURATION", "2.0"))


def _port_is_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def _resolve_agent_port() -> int:
    raw_port = os.getenv("WID_WINS_AGENT_PORT", "8081").strip()
    try:
        preferred_port = int(raw_port)
    except ValueError as exc:
        raise ValueError("WID_WINS_AGENT_PORT must be an integer between 0 and 65535.") from exc

    if preferred_port < 0 or preferred_port > 65535:
        raise ValueError("WID_WINS_AGENT_PORT must be between 0 and 65535.")

    if preferred_port == 0 or _port_is_available(preferred_port):
        return preferred_port

    for candidate in range(preferred_port + 1, min(preferred_port + 50, 65535) + 1):
        if _port_is_available(candidate):
            print(
                f"WID_WINS_AGENT_PORT={preferred_port} is already in use; "
                f"starting on fallback port {candidate}."
            )
            return candidate

    print(
        f"WID_WINS_AGENT_PORT={preferred_port} is already in use and no nearby port was free; "
        "starting with an OS-assigned port."
    )
    return 0


def _build_stt_backend():
    if STT_BACKEND == INFERENCE_BACKEND:
        return inference.STT(STT_MODEL, language=STT_LANGUAGE)

    if STT_BACKEND == DEEPGRAM_BACKEND:
        if deepgram is None:
            raise RuntimeError(
                "WID_WINS_STT_BACKEND=deepgram requires the Deepgram plugin. "
                "Install with: pip install 'livekit-agents[deepgram]~=1.4'"
            )
        return deepgram.STT(model=STT_PLUGIN_MODEL, language=STT_LANGUAGE)

    raise RuntimeError(f"Unsupported STT backend: {STT_BACKEND}")


def _is_text_only_mode() -> bool:
    return os.getenv("WID_WINS_TEXT_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}


def _build_llm_backend():
    backend = os.getenv("WID_WINS_LLM_BACKEND", "inference").strip().lower()
    if backend == "stub":
        return LocalStubLLM()
    if backend == "inference":
        model = os.getenv("WID_WINS_LLM_MODEL", "openai/gpt-4o-mini").strip() or "openai/gpt-4o-mini"
        return inference.LLM(model)
    raise RuntimeError(
        "Unsupported WID_WINS_LLM_BACKEND value. Use one of: inference, stub."
    )


@function_tool
async def assess_lead(
    context: RunContext,
    idea_summary: str = "",
    problem: str = "",
    target_users: str = "",
    primary_goal: str = "",
    current_stage: str = "",
    budget: str = "",
    timeline: str = "",
    commitment_level: str = "",
):
    """Assess a Wid Wins lead, identify missing details, suggest the best-fit package, and guide the next step."""

    profile = LeadProfile(
        idea_summary=idea_summary,
        problem=problem,
        target_users=target_users,
        primary_goal=primary_goal,
        current_stage=current_stage,
        budget=budget,
        timeline=timeline,
        commitment_level=commitment_level,
    )
    return build_lead_assessment(profile)


@function_tool
async def capture_lead(
    context: RunContext,
    full_name: str = "",
    idea_summary: str = "",
    lead_type: str = "",
    recommended_package: str = "",
    email: str = "",
    phone: str = "",
    problem: str = "",
    target_users: str = "",
    primary_goal: str = "",
    current_stage: str = "",
    budget: str = "",
    timeline: str = "",
    commitment_level: str = "",
    conversation_summary: str = "",
    notes: str = "",
):
    """Save a qualified Wid Wins lead with contact details and a concise handoff summary."""

    saved_to = save_lead(
        {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "lead_type": lead_type,
            "recommended_package": recommended_package,
            "idea_summary": idea_summary,
            "problem": problem,
            "target_users": target_users,
            "primary_goal": primary_goal,
            "current_stage": current_stage,
            "budget": budget,
            "timeline": timeline,
            "commitment_level": commitment_level,
            "conversation_summary": conversation_summary,
            "notes": notes,
        }
    )
    return {
        "status": "saved",
        "saved_to": str(saved_to),
        "message": "Lead captured for Wid Wins follow-up.",
    }


AGENT_HOST = os.getenv("WID_WINS_AGENT_HOST", "")
AGENT_PORT = _resolve_agent_port()
server = AgentServer(host=AGENT_HOST, port=AGENT_PORT)


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    text_only_mode = _is_text_only_mode()
    session_kwargs = {
        "llm": _build_llm_backend(),
    }

    if not text_only_mode:
        session_kwargs.update(
            {
                "vad": silero.VAD.load(),
                "stt": _build_stt_backend(),
                "tts": inference.TTS(
                    model=TTS_MODEL,
                    voice=TTS_VOICE,
                    language=TTS_LANGUAGE,
                    extra_kwargs={"speed": TTS_SPEED},
                ),
                "use_tts_aligned_transcript": True,
                "aec_warmup_duration": AEC_WARMUP_DURATION,
                "turn_handling": {
                    "turn_detection": TURN_DETECTION,
                    "endpointing": {
                        "min_delay": MIN_ENDPOINTING_DELAY,
                        "max_delay": 0.5,
                    },
                    "interruption": {
                        "enabled": True,
                        "discard_audio_if_uninterruptible": True,
                        "min_duration": MIN_INTERRUPTION_DURATION,
                        "false_interruption_timeout": FALSE_INTERRUPTION_TIMEOUT,
                    },
                },
            }
        )

    session = AgentSession(**session_kwargs)

    agent = Agent(
        instructions=AGENT_INSTRUCTIONS,
        tools=[assess_lead, capture_lead],
    )

    room_options = None
    if not text_only_mode and noise_cancellation is not None:
        room_options = room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            )
        )

    await session.start(agent=agent, room=ctx.room, room_options=room_options)
    await session.generate_reply(
        instructions=(
            "Welcome the caller in one short sentence, mention Wid Wins helps founders turn ideas into structured "
            "business direction, and ask only one simple question about their idea or current challenge."
        ),
        allow_interruptions=False,
    )


if __name__ == "__main__":
    configure_utf8_stdio()

    # For local console runs, default to text mode with inference LLM unless explicitly overridden.
    if len(sys.argv) > 1 and sys.argv[1] == "console":
        has_text_flag = "--text" in sys.argv or "--no-text" in sys.argv
        if not has_text_flag:
            sys.argv.append("--text")
            os.environ.setdefault("WID_WINS_TEXT_ONLY", "1")
        if "--text" in sys.argv:
            os.environ.setdefault("WID_WINS_TEXT_ONLY", "1")
            os.environ.setdefault("WID_WINS_LLM_BACKEND", "inference")

    cli.run_app(server)
