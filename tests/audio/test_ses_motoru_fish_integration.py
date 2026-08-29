import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ultron.audio import ses_motoru


class GetAudioFishIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self._tmp_dir, ignore_errors=True)

    async def test_uses_cached_fish_audio_file_when_present(self):
        with patch("ultron.audio.ses_motoru.fish_cache_path") as mock_path:
            cache_file = self._tmp_dir / "cached.mp3"
            cache_file.write_bytes(b"cached-fish-bytes")
            mock_path.return_value = cache_file

            result = await ses_motoru._get_audio("some text")

        self.assertEqual(result, b"cached-fish-bytes")

    async def test_live_fish_synthesis_is_used_and_cached_when_enabled(self):
        cache_file = self._tmp_dir / "new.mp3"
        with (
            patch("ultron.audio.ses_motoru.fish_cache_path", return_value=cache_file),
            patch("ultron.audio.ses_motoru.fish_enabled", return_value=True),
            patch("ultron.audio.ses_motoru.fish_synthesize", return_value=b"live-fish-bytes") as mock_synth,
            patch("ultron.audio.ses_motoru._synthesize") as mock_edge_synth,
        ):
            result = await ses_motoru._get_audio("brand new dynamic text")

        self.assertEqual(result, b"live-fish-bytes")
        mock_synth.assert_called_once_with("brand new dynamic text")
        mock_edge_synth.assert_not_called()
        self.assertEqual(cache_file.read_bytes(), b"live-fish-bytes")

    async def test_falls_back_to_edge_tts_when_fish_synthesis_fails(self):
        cache_file = self._tmp_dir / "missing.mp3"
        with (
            patch("ultron.audio.ses_motoru.fish_cache_path", return_value=cache_file),
            patch("ultron.audio.ses_motoru.fish_enabled", return_value=True),
            patch("ultron.audio.ses_motoru.fish_synthesize", return_value=None),
            patch("ultron.audio.ses_motoru._cache_path", return_value=self._tmp_dir / "edge_cache.mp3"),
            patch("ultron.audio.ses_motoru._synthesize", return_value=b"edge-tts-bytes") as mock_edge_synth,
        ):
            result = await ses_motoru._get_audio("some text")

        self.assertEqual(result, b"edge-tts-bytes")
        mock_edge_synth.assert_called_once()

    async def test_falls_back_to_edge_tts_when_fish_disabled(self):
        cache_file = self._tmp_dir / "missing2.mp3"
        with (
            patch("ultron.audio.ses_motoru.fish_cache_path", return_value=cache_file),
            patch("ultron.audio.ses_motoru.fish_enabled", return_value=False),
            patch("ultron.audio.ses_motoru.fish_synthesize") as mock_synth,
            patch("ultron.audio.ses_motoru._cache_path", return_value=self._tmp_dir / "edge_cache2.mp3"),
            patch("ultron.audio.ses_motoru._synthesize", return_value=b"edge-tts-bytes") as mock_edge_synth,
        ):
            result = await ses_motoru._get_audio("some text")

        self.assertEqual(result, b"edge-tts-bytes")
        mock_synth.assert_not_called()
        mock_edge_synth.assert_called_once()


if __name__ == "__main__":
    unittest.main()
