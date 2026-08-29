import time
import unittest

import numpy as np

from ultron.runtime import wake_listener


class _FakeAudio:
    def __init__(self, samples: np.ndarray):
        self._raw = samples.astype(np.int16).tobytes()

    def get_raw_data(self):
        return self._raw


class MicLevelTests(unittest.TestCase):
    def test_silence_reports_near_zero_level(self):
        level = wake_listener._update_mic_level(_FakeAudio(np.zeros(1600)))

        self.assertAlmostEqual(level, 0.0, places=3)
        self.assertAlmostEqual(wake_listener.get_mic_level(), 0.0, places=3)

    def test_loud_audio_reports_a_high_level(self):
        loud = np.full(1600, 20000)

        level = wake_listener._update_mic_level(_FakeAudio(loud))

        self.assertGreater(level, 0.5)
        self.assertAlmostEqual(wake_listener.get_mic_level(), level, places=3)

    def test_level_clamped_to_one(self):
        clipping = np.full(1600, 32767)

        level = wake_listener._update_mic_level(_FakeAudio(clipping))

        self.assertLessEqual(level, 1.0)

    def test_stale_level_reports_zero(self):
        wake_listener._update_mic_level(_FakeAudio(np.full(1600, 20000)))

        self.assertEqual(wake_listener.get_mic_level(max_age=0.0), 0.0)

    def test_fresh_level_is_not_stale(self):
        wake_listener._update_mic_level(_FakeAudio(np.full(1600, 20000)))

        self.assertGreater(wake_listener.get_mic_level(max_age=5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
