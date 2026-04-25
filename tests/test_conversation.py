import unittest

from conversation import build_direct_reply, create_profile


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

        reply = build_direct_reply("contact_shared", "My email is aakash@example.com", profile)

        self.assertIn("Thanks", reply)
        self.assertIn("contact you soon", reply)


if __name__ == "__main__":
    unittest.main()
