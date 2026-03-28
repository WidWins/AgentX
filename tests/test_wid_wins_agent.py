import unittest
from pathlib import Path

from wid_wins_agent import (
    AGENT_INSTRUCTIONS,
    KNOWLEDGE_BASE_TEXT,
    LeadProfile,
    build_capture_prompt,
    build_conversation_summary,
    build_follow_up_message,
    build_lead_assessment,
    classify_lead,
    recommend_package,
)


class WidWinsAgentTests(unittest.TestCase):
    def test_knowledge_base_is_loaded(self) -> None:
        self.assertIn("Wid Wins", KNOWLEDGE_BASE_TEXT)
        self.assertIn("Rising Dreams into Reality", KNOWLEDGE_BASE_TEXT)

    def test_voice_rules_are_present_in_instructions(self) -> None:
        self.assertIn("Speak in short, natural sentences.", AGENT_INSTRUCTIONS)
        self.assertIn("Ask only one question at a time.", AGENT_INSTRUCTIONS)
        self.assertIn("Use plain spoken English suitable for live business conversations.", AGENT_INSTRUCTIONS)

    def test_test_env_contains_stability_defaults(self) -> None:
        env_path = Path("tests/.env")
        if not env_path.exists():
            self.skipTest("tests/.env not found; skipping environment stability check.")
            
        env_text = env_path.read_text(encoding="utf-8")
        self.assertIn("WID_WINS_TURN_DETECTION=vad", env_text)
        self.assertIn("WID_WINS_MIN_ENDPOINTING_DELAY=0.1", env_text)
        self.assertIn("WID_WINS_MIN_INTERRUPTION_DURATION=0.1", env_text)
        self.assertIn("WID_WINS_FALSE_INTERRUPTION_TIMEOUT=2.0", env_text)
        self.assertIn("WID_WINS_AEC_WARMUP_DURATION=2.0", env_text)

    def test_voice_agent_uses_noise_cancellation_and_fixed_elevenlabs_voice(self) -> None:
        voice_agent_text = Path("voice_agent.py").read_text(encoding="utf-8")
        self.assertIn('TTS_MODEL = "elevenlabs/eleven_flash_v2_5"', voice_agent_text)
        self.assertIn('TTS_VOICE = "Xb7hH8MSUJpSbSDYk0k2"', voice_agent_text)
        self.assertIn('noise_cancellation.BVC()', voice_agent_text)
        self.assertIn('room_options=room_options', voice_agent_text)
        self.assertIn('os.environ.setdefault("WID_WINS_LLM_BACKEND", "inference")', voice_agent_text)
        self.assertNotIn('os.environ.setdefault("WID_WINS_LLM_BACKEND", "stub")', voice_agent_text)

    def test_high_intent_lead_gets_premium_package(self) -> None:
        profile = LeadProfile(
            idea_summary="AI assistant for clinic operations",
            problem="Small clinics lose time on manual scheduling",
            target_users="Clinic owners",
            primary_goal="Launch a pilot in 60 days",
            current_stage="execution",
            budget="premium",
            timeline="ready to launch this quarter",
            commitment_level="serious and ready to invest",
        )

        self.assertEqual(classify_lead(profile), "high_intent")
        self.assertEqual(recommend_package(profile), "Premium")
        self.assertIn("Premium", build_follow_up_message(profile))
        self.assertIn("contact method", build_capture_prompt(profile))

    def test_qualified_lead_gets_standard_package(self) -> None:
        profile = LeadProfile(
            idea_summary="Marketplace for local tutors",
            problem="Parents struggle to find trusted tutors nearby",
            target_users="Parents of school students",
            primary_goal="Validate demand and create a business roadmap",
            current_stage="planning",
            budget="standard",
            timeline="within the next few months",
            commitment_level="committed to moving forward",
        )

        self.assertEqual(classify_lead(profile), "qualified")
        self.assertEqual(recommend_package(profile), "Standard")
        self.assertIn("Standard", build_follow_up_message(profile))

    def test_missing_core_fields_returns_follow_up_questions(self) -> None:
        profile = LeadProfile(
            idea_summary="Education app for rural learners",
            primary_goal="Understand whether this can become a real startup",
        )

        assessment = build_lead_assessment(profile)

        self.assertEqual(assessment["lead_type"], "needs_more_info")
        self.assertFalse(assessment["capture_recommended"])
        self.assertIn("problem being solved", assessment["missing_fields"])
        self.assertIn("target users", assessment["missing_fields"])
        self.assertGreaterEqual(len(assessment["next_questions"]), 2)
        self.assertIn("Do not ask for contact details yet", assessment["capture_prompt"])

    def test_low_intent_lead_is_flagged_politely(self) -> None:
        profile = LeadProfile(
            idea_summary="Fashion brand idea",
            problem="Need help shaping the brand",
            target_users="College students",
            primary_goal="Just exploring free advice for now",
            current_stage="idea",
            budget="no budget ever",
            commitment_level="just curious",
        )

        self.assertEqual(classify_lead(profile), "low_intent")
        self.assertEqual(recommend_package(profile), "Basic")
        self.assertNotIn("Basic", build_follow_up_message(profile))

    def test_qualified_lead_recommends_capture(self) -> None:
        profile = LeadProfile(
            idea_summary="Operations tool for local restaurants",
            problem="Restaurants lose time coordinating staff and orders",
            target_users="Independent restaurant owners",
            primary_goal="Validate demand and map a launch plan",
            current_stage="planning",
            budget="standard",
            timeline="next quarter",
            commitment_level="serious",
        )

        assessment = build_lead_assessment(profile)

        self.assertEqual(assessment["lead_type"], "qualified")
        self.assertTrue(assessment["capture_recommended"])
        self.assertIn("Standard", assessment["capture_prompt"])

    def test_conversation_summary_contains_key_fields(self) -> None:
        profile = LeadProfile(
            idea_summary="Scheduling tool for salons",
            problem="Salon owners lose time managing appointments manually",
            target_users="Independent salon owners",
            primary_goal="Validate demand before building",
            current_stage="planning",
            budget="basic",
            timeline="this summer",
            commitment_level="curious but serious",
        )

        summary = build_conversation_summary(profile)

        self.assertIn("Idea: Scheduling tool for salons", summary)
        self.assertIn("Problem: Salon owners lose time managing appointments manually", summary)
        self.assertIn("Target users: Independent salon owners", summary)


if __name__ == "__main__":
    unittest.main()

