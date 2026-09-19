import unittest
from unittest.mock import patch

from ultron.audio.wake_word import build_wake_word_config
from ultron.runtime import wake_listener


class OnlineConfirmationMatchTests(unittest.TestCase):
    def setUp(self):
        # Deterministic config regardless of ambient .env state / import
        # order - other tests build their own config explicitly for the
        # same reason (see test_wake_word_detection.py).
        config = build_wake_word_config({"JARVIS_WAKE_WORD": "ultron"})
        patcher = patch.object(wake_listener, "WAKE_WORD_CONFIG", config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exact_wake_word_matches(self):
        self.assertEqual(wake_listener._online_confirmation_match("Ultron"), "ultron")
        self.assertEqual(wake_listener._online_confirmation_match("the Ultron"), "ultron")

    def test_bare_ultra_is_accepted_as_a_clipped_ultron(self):
        # Confirmed from real usage logs: Google's recognizer repeatedly
        # clips the trailing "n" off a genuine "Ultron" utterance.
        self.assertEqual(wake_listener._online_confirmation_match("Ultra"), "ultra")
        self.assertEqual(wake_listener._online_confirmation_match("oh Ultra"), "ultra")

    def test_ultra_as_part_of_another_word_does_not_match(self):
        self.assertIsNone(wake_listener._online_confirmation_match("ultraviolet"))
        self.assertIsNone(wake_listener._online_confirmation_match("ultramarathon"))

    def test_unrelated_speech_does_not_match(self):
        self.assertIsNone(wake_listener._online_confirmation_match("level two"))
        self.assertIsNone(wake_listener._online_confirmation_match(""))
        self.assertIsNone(wake_listener._online_confirmation_match("that was a nice movie"))

    def test_alternate_name_matches_and_is_flagged_for_the_correction_greeting(self):
        self.assertEqual(wake_listener._online_confirmation_match("Jarvis"), "jarvis")
        self.assertEqual(wake_listener._greeting_for("jarvis"), wake_listener.ALTERNATE_NAME_GREETING)
        self.assertEqual(wake_listener._greeting_for("ultron"), wake_listener.DEFAULT_GREETING)


if __name__ == "__main__":
    unittest.main()
