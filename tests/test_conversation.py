import unittest

from conversation import build_direct_reply, build_refined_idea_summary, build_refinement_question, create_profile


class ConversationFlowTests(unittest.TestCase):
    def test_idea_message_triggers_contact_handoff(self) -> None:
        profile = create_profile()
        profile["goal"] = "Build an app for clinics"

        reply = build_direct_reply("discovery", "I want to build an app for clinics", profile)

        self.assertIn("noted your idea", reply)
        self.assertIn("contact details", reply)

    def test_contact_details_trigger_confirmation(self) -> None:
        profile = create_profile()
        profile["name"] = "Aakash"
        profile["idea_summary"] = "Fitness app for busy workers"
        profile["goal"] = "build a simple app"

        reply = build_direct_reply(
            "contact_shared",
            "My email is aakash@example.com",
            profile,
            ["I want a fitness app", "My email is aakash@example.com"],
        )

        self.assertIn("Thanks", reply)
        self.assertIn("refine it better", reply)

    def test_refined_summary_uses_history(self) -> None:
        profile = create_profile()
        profile["idea_summary"] = "Fitness app for busy workers"
        profile["target_customer"] = "busy workers"
        profile["problem"] = "they miss workouts"
        profile["email"] = "peter@example.com"

        summary = build_refined_idea_summary(
            profile,
            [
                {"role": "user", "text": "I want a fitness app"},
                {"role": "assistant", "text": "What problem does it solve?"},
                {"role": "user", "text": "It helps busy workers stay fit"},
            ],
        )

        self.assertIn("Idea: Fitness app for busy workers", summary)
        self.assertIn("History:", summary)
        self.assertIn("assistant:", summary)
        self.assertIn("user:", summary)

    def test_refinement_question_returns_simple_next_step(self) -> None:
        profile = create_profile()
        profile["idea_summary"] = "Fitness app"

        question = build_refinement_question(profile, [])

        self.assertTrue(question)
        self.assertIn("problem", question.lower())


if __name__ == "__main__":
    unittest.main()
