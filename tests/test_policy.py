import unittest

from qwenapi.policy import classify_query


class PolicyTests(unittest.TestCase):
    def test_high_stakes_is_mandatory_even_when_off(self):
        result = classify_query("What does Philippine law say about contracts?", "off")
        self.assertEqual(result.category, "legal")
        self.assertEqual(result.policy, "required")
        self.assertTrue(result.mandatory)

    def test_source_only_mode_for_general_question(self):
        result = classify_query("Summarize this supplied project brief", "source_only")
        self.assertEqual(result.policy, "source_only")
        self.assertFalse(result.mandatory)

    def test_unknown_mode_fails_safe(self):
        result = classify_query("Tell me about this topic", "not-a-mode")
        self.assertEqual(result.policy, "required")


if __name__ == "__main__":
    unittest.main()
