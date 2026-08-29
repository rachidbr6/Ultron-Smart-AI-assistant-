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
        self.assertTrue(wake_listener._online_confirmation_matches("Ultron"))
        self.assertTrue(wake_listener._online_confirmation_matches("the Ultron"))

    def test_bare_ultra_is_accepted_as_a_clipped_ultron(self):
        # Confirmed from real usage logs: Google's recognizer repeatedly
        # clips the trailing "n" off a genuine "Ultron" utterance.
        self.assertTrue(wake_listener._online_confirmation_matches("Ultra"))
        self.assertTrue(wake_listener._online_confirmation_matches("oh Ultra"))

    def test_ultra_as_part_of_another_word_does_not_match(self):
        self.assertFalse(wake_listener._online_confirmation_matches("ultraviolet"))
        self.assertFalse(wake_listener._online_confirmation_matches("ultramarathon"))

    def test_unrelated_speech_does_not_match(self):
        self.assertFalse(wake_listener._online_confirmation_matches("level two"))
        self.assertFalse(wake_listener._online_confirmation_matches(""))
        self.assertFalse(wake_listener._online_confirmation_matches("that was a nice movie"))


if __name__ == "__main__":
    unittest.main()
