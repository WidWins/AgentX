import unittest

from stt_config import (
    DEEPGRAM_BACKEND,
    INFERENCE_BACKEND,
    default_deepgram_plugin_model,
    normalize_stt_backend,
    resolve_stt_settings,
)


class SttConfigTests(unittest.TestCase):
    def test_defaults_match_inference_setup(self) -> None:
        settings = resolve_stt_settings({})
        self.assertEqual(settings["backend"], INFERENCE_BACKEND)
        self.assertEqual(settings["language"], "en-IN")
        self.assertEqual(settings["inference_model"], "deepgram/nova-3")
        self.assertEqual(settings["plugin_model"], "nova-3")

    def test_normalize_backend_supports_aliases(self) -> None:
        self.assertEqual(normalize_stt_backend("livekit"), INFERENCE_BACKEND)
        self.assertEqual(normalize_stt_backend("livekit_inference"), INFERENCE_BACKEND)
        self.assertEqual(normalize_stt_backend("plugin"), DEEPGRAM_BACKEND)
        self.assertEqual(normalize_stt_backend("deepgram_plugin"), DEEPGRAM_BACKEND)

    def test_invalid_backend_raises_helpful_error(self) -> None:
        with self.assertRaises(ValueError):
            normalize_stt_backend("invalid-backend")

    def test_deepgram_plugin_model_strips_provider_prefix(self) -> None:
        self.assertEqual(default_deepgram_plugin_model("deepgram/nova-3"), "nova-3")
        self.assertEqual(default_deepgram_plugin_model("nova-3"), "nova-3")
        self.assertEqual(default_deepgram_plugin_model(""), "nova-3")

    def test_resolve_settings_prefers_explicit_plugin_model(self) -> None:
        settings = resolve_stt_settings(
            {
                "WID_WINS_STT_BACKEND": "deepgram",
                "WID_WINS_STT_MODEL": "deepgram/nova-3-medical",
                "WID_WINS_STT_PLUGIN_MODEL": "nova-2",
                "WID_WINS_STT_LANGUAGE": "en-US",
            }
        )
        self.assertEqual(settings["backend"], DEEPGRAM_BACKEND)
        self.assertEqual(settings["language"], "en-US")
        self.assertEqual(settings["inference_model"], "deepgram/nova-3-medical")
        self.assertEqual(settings["plugin_model"], "nova-2")


if __name__ == "__main__":
    unittest.main()
