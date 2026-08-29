import unittest
from unittest.mock import MagicMock, patch

from ultron.audio import fish_tts


class FishTtsTests(unittest.TestCase):
    def test_disabled_without_key_or_voice(self):
        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "", "FISH_AUDIO_VOICE_ID": ""}):
            self.assertFalse(fish_tts.fish_enabled())
            self.assertIsNone(fish_tts.synthesize("hello"))

    def test_enabled_requires_both_key_and_voice_id(self):
        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "key", "FISH_AUDIO_VOICE_ID": ""}):
            self.assertFalse(fish_tts.fish_enabled())
        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "", "FISH_AUDIO_VOICE_ID": "voice"}):
            self.assertFalse(fish_tts.fish_enabled())
        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "key", "FISH_AUDIO_VOICE_ID": "voice"}):
            self.assertTrue(fish_tts.fish_enabled())

    @patch("ultron.audio.fish_tts.requests.post")
    def test_synthesize_returns_bytes_on_success(self, mock_post):
        mock_response = MagicMock(status_code=200, content=b"fake-mp3-bytes")
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "key", "FISH_AUDIO_VOICE_ID": "voice"}):
            result = fish_tts.synthesize("At your service, sir.")

        self.assertEqual(result, b"fake-mp3-bytes")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["reference_id"], "voice")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer key")

    @patch("ultron.audio.fish_tts.requests.post")
    def test_synthesize_returns_none_on_http_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500, content=b"")

        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "key", "FISH_AUDIO_VOICE_ID": "voice"}):
            self.assertIsNone(fish_tts.synthesize("hello"))

    @patch("ultron.audio.fish_tts.requests.post", side_effect=Exception("boom"))
    def test_synthesize_returns_none_on_request_exception(self, mock_post):
        import requests

        mock_post.side_effect = requests.RequestException("network down")
        with patch.dict("os.environ", {"FISH_AUDIO_API_KEY": "key", "FISH_AUDIO_VOICE_ID": "voice"}):
            self.assertIsNone(fish_tts.synthesize("hello"))

    def test_cache_path_is_stable_for_same_text_and_voice(self):
        with patch.dict("os.environ", {"FISH_AUDIO_VOICE_ID": "voice-a"}):
            path1 = fish_tts.fish_cache_path("hello there")
            path2 = fish_tts.fish_cache_path("hello there")
        self.assertEqual(path1, path2)

    def test_cache_path_differs_for_different_text(self):
        with patch.dict("os.environ", {"FISH_AUDIO_VOICE_ID": "voice-a"}):
            path1 = fish_tts.fish_cache_path("hello there")
            path2 = fish_tts.fish_cache_path("goodbye there")
        self.assertNotEqual(path1, path2)


if __name__ == "__main__":
    unittest.main()
