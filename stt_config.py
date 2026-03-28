from __future__ import annotations

import os
from collections.abc import Mapping

INFERENCE_BACKEND = "inference"
DEEPGRAM_BACKEND = "deepgram"

_BACKEND_ALIASES = {
    "inference": INFERENCE_BACKEND,
    "livekit": INFERENCE_BACKEND,
    "livekit_inference": INFERENCE_BACKEND,
    "deepgram": DEEPGRAM_BACKEND,
    "deepgram_plugin": DEEPGRAM_BACKEND,
    "plugin": DEEPGRAM_BACKEND,
}


def normalize_stt_backend(raw_backend: str | None) -> str:
    backend_value = (raw_backend or INFERENCE_BACKEND).strip().lower()
    if not backend_value:
        backend_value = INFERENCE_BACKEND

    backend = _BACKEND_ALIASES.get(backend_value)
    if backend is None:
        raise ValueError(
            "Unsupported WID_WINS_STT_BACKEND value. Use one of: "
            "inference, livekit, livekit_inference, deepgram, deepgram_plugin, plugin."
        )
    return backend


def default_deepgram_plugin_model(stt_model: str) -> str:
    cleaned_model = stt_model.strip()
    if cleaned_model.lower().startswith("deepgram/"):
        return cleaned_model.split("/", 1)[1]
    return cleaned_model or "nova-3"


def resolve_stt_settings(env: Mapping[str, str] | None = None) -> dict[str, str]:
    source = env if env is not None else os.environ

    inference_model = source.get("WID_WINS_STT_MODEL", "deepgram/nova-3")
    settings = {
        "backend": normalize_stt_backend(source.get("WID_WINS_STT_BACKEND")),
        "language": source.get("WID_WINS_STT_LANGUAGE", "en-IN"),
        "inference_model": inference_model,
        "plugin_model": source.get(
            "WID_WINS_STT_PLUGIN_MODEL",
            default_deepgram_plugin_model(inference_model),
        ),
    }
    return settings
