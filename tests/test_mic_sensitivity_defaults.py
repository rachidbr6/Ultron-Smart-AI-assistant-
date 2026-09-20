"""Coverage for the wake/command listeners' microphone sensitivity defaults.

Both recognizers read their tuning from a couple of env vars at import time,
so these tests reload the modules under a controlled environment rather than
inspecting already-imported singletons.
"""

from __future__ import annotations

import importlib
import os
import unittest

_ENV_KEYS = ("JARVIS_ENERGY_THRESHOLD", "JARVIS_PAUSE_THRESHOLD")


def _reload_with_env(module_name: str, overrides: dict[str, str]):
    module = importlib.import_module(module_name)
    saved = {key: os.environ.pop(key, None) for key in _ENV_KEYS}
    os.environ.update(overrides)
    try:
        importlib.reload(module)
    finally:
        for key in _ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in saved.items():
            if value is not None:
                os.environ[key] = value
    return module


class MicSensitivityDefaultsTest(unittest.TestCase):
    def tearDown(self):
        # Reload both modules against the real process environment so a
        # test-mutated state never leaks into tests that run after this one.
        import ultron.runtime.command_listener as command_listener
        import ultron.runtime.wake_listener as wake_listener

        importlib.reload(command_listener)
        importlib.reload(wake_listener)

    def test_wake_listener_defaults_to_a_sensitive_energy_threshold(self):
        module = _reload_with_env("ultron.runtime.wake_listener", {})

        self.assertEqual(module._wake_recognizer.energy_threshold, 150)

    def test_command_listener_matches_the_wake_listener_default(self):
        module = _reload_with_env("ultron.runtime.command_listener", {})

        self.assertEqual(module._cmd_recognizer.energy_threshold, 150)

    def test_energy_threshold_env_override_applies_to_both_listeners(self):
        wake = _reload_with_env("ultron.runtime.wake_listener", {"JARVIS_ENERGY_THRESHOLD": "80"})
        command = _reload_with_env("ultron.runtime.command_listener", {"JARVIS_ENERGY_THRESHOLD": "80"})

        self.assertEqual(wake._wake_recognizer.energy_threshold, 80)
        self.assertEqual(command._cmd_recognizer.energy_threshold, 80)

    def test_wake_listener_pause_threshold_is_configurable(self):
        module = _reload_with_env("ultron.runtime.wake_listener", {"JARVIS_PAUSE_THRESHOLD": "0.35"})

        self.assertEqual(module._wake_recognizer.pause_threshold, 0.35)


if __name__ == "__main__":
    unittest.main()
