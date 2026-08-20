from unittest import TestCase

from open_jarvis.audio.wake_word import (
    WakeWordDetector,
    build_wake_word_config,
    fuzzy_wake_word_score,
    normalize_voice_phrase,
    wake_word_detected,
)


class WakeWordDetectionTest(TestCase):
    def test_detects_configured_wake_word_with_case_and_punctuation(self):
        self.assertTrue(wake_word_detected("Hey, JARVIS!", wake_word="jarvis"))

    def test_does_not_match_unsafe_substring(self):
        self.assertFalse(wake_word_detected("scarjarvisthing", wake_word="jarvis"))

    def test_disabled_wake_word_config_never_detects(self):
        config = build_wake_word_config({"JARVIS_WAKE_WORD": "friday", "JARVIS_WAKE_WORD_ENABLED": "false"})

        self.assertFalse(wake_word_detected("friday", config=config))
        self.assertFalse(config["enabled"])

    def test_detector_applies_cooldown(self):
        detector = WakeWordDetector(wake_word="jarvis", cooldown_seconds=2.0, clock=lambda: 10.0)

        self.assertTrue(detector.detect("jarvis")["detected"])
        self.assertFalse(detector.detect("jarvis")["detected"])

    def test_normalize_voice_phrase_collapses_noise(self):
        self.assertEqual(normalize_voice_phrase("  Hey,   Jarvis!!! "), "hey jarvis")

    def test_fuzzy_wake_word_score_flags_likely_mishearings_of_an_unusual_word(self):
        # A compact offline STT model without "ultron" in its vocabulary
        # tends to substitute a similar-sounding real word or words - these
        # should score high enough to be worth an online confirmation pass.
        self.assertGreaterEqual(fuzzy_wake_word_score("all tron", "ultron"), 0.5)
        self.assertGreaterEqual(fuzzy_wake_word_score("outrun", "ultron"), 0.5)
        self.assertGreaterEqual(fuzzy_wake_word_score("hail tron", "ultron"), 0.5)

    def test_fuzzy_wake_word_score_ignores_clearly_unrelated_speech(self):
        self.assertLess(fuzzy_wake_word_score("open chrome", "ultron"), 0.5)
        self.assertLess(fuzzy_wake_word_score("good morning", "ultron"), 0.5)

    def test_fuzzy_wake_word_score_empty_input_is_zero(self):
        self.assertEqual(fuzzy_wake_word_score("", "ultron"), 0.0)
        self.assertEqual(fuzzy_wake_word_score("ultron", ""), 0.0)
