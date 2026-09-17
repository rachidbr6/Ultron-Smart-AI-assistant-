import unittest

from ultron.commands.local_intent_router import normalize_command, route_local_intent


class LocalIntentRouterTests(unittest.TestCase):
    def test_normalize_command_handles_case_and_spacing(self):
        self.assertEqual(normalize_command("  OPEN   CHROME   "), "open chrome")

    def test_routes_system_status_commands_without_llm(self):
        cases = {
            "what time is it": "get_time",
            "what date is it": "get_date",
            "cpu usage": "get_cpu",
            "memory usage": "get_ram",
            "battery status": "get_battery",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertIsNotNone(result)
                self.assertEqual(result["action"], action)

    def test_routes_desktop_utility_commands_without_llm(self):
        cases = {
            "take screenshot": "screenshot",
            "read clipboard": "read_clipboard",
            "summarize clipboard": "summarize_clipboard",
            "read notes": "read_notes",
            "memory stats": "memory_stats",
            "memory habits": "memory_habits",
            "clean memory": "prune_memory",
            "daily summary": "daily_summary",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertIsNotNone(result)
                self.assertEqual(result["action"], action)

    def test_routes_open_app_with_supported_application(self):
        result = route_local_intent("open chrome")

        self.assertEqual(result["action"], "open_app")
        self.assertEqual(result["params"], {"app": "chrome"})

    def test_routes_google_search_and_extracts_query(self):
        result = route_local_intent("google open source AI architecture")

        self.assertEqual(result["action"], "search_google")
        self.assertEqual(result["params"], {"query": "open source ai architecture"})

    def test_routes_general_search_phrases_and_extracts_query(self):
        cases = {
            "search for python desktop assistant": "python desktop assistant",
            "look up groq free api": "groq free api",
            "find jarvis ui inspiration": "jarvis ui inspiration",
        }

        for command, query in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "search_google")
                self.assertEqual(result["params"], {"query": query})

    def test_routes_open_web_for_known_sites_and_urls(self):
        cases = {
            "open youtube": "https://www.youtube.com",
            "open github": "https://github.com",
            "open https://example.com/docs": "https://example.com/docs",
            "go to openai.com": "https://openai.com",
        }

        for command, url in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "open_web")
                self.assertEqual(result["params"], {"url": url})

    def test_routes_mail_phrasing_to_gmail_with_a_mail_flavored_response(self):
        from ultron.runtime.voice_personality import MAIL_INTROS

        for command in ("open mail", "open email", "open my mail", "check my email", "open gmail"):
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "open_web")
                self.assertEqual(result["params"], {"url": "https://mail.google.com"})
                self.assertIn(result["response"], MAIL_INTROS)

    def test_routes_weather_phrasing_to_get_weather(self):
        for command in ("weather", "what's the weather", "weather today", "how's the weather"):
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "get_weather")

    def test_mentioning_stark_triggers_a_stark_reaction(self):
        from ultron.runtime.voice_personality import STARK_REACTIONS

        for command in ("what do you think of tony stark", "is stark a hero", "tell me about iron man"):
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "talk")
                self.assertIn(result["response"], STARK_REACTIONS)

    def test_asking_about_the_world_triggers_a_world_opinion(self):
        from ultron.runtime.voice_personality import WORLD_OPINION_LINES

        for command in ("what do you think of the world", "how do you feel about the world", "tell me about the world"):
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], "talk")
                self.assertIn(result["response"], WORLD_OPINION_LINES)

    def test_routes_window_and_volume_controls_without_llm(self):
        cases = {
            "minimize all windows": ("minimize_all", {}),
            "maximize window": ("maximize_window", {}),
            "close current window": ("close_window", {}),
            "mute volume": ("press_key", {"key": "volumemute"}),
            "volume up": ("press_key", {"key": "volumeup"}),
            "turn volume down": ("press_key", {"key": "volumedown"}),
        }

        for command, expected in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual((result["action"], result["params"]), expected)

    def test_routes_spotify_controls_without_llm(self):
        cases = {
            "play music": "spotify_play",
            "pause music": "spotify_pause",
            "next track": "spotify_next",
            "previous song": "spotify_prev",
            "what is playing on spotify": "spotify_current",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertEqual(result["action"], action)

    def test_routes_add_note_and_extracts_note_text(self):
        result = route_local_intent("add note run tests tomorrow")

        self.assertEqual(result["action"], "add_note")
        self.assertEqual(result["params"], {"text": "run tests tomorrow"})

    def test_routes_power_and_lock_commands_without_llm(self):
        cases = {
            "lock my laptop": "lock_screen",
            "lock the screen": "lock_screen",
            "shutdown": "shutdown",
            "shut down my laptop": "shutdown",
            "turn off my laptop": "shutdown",
            "restart my laptop": "restart",
            "reboot": "restart",
            "go to sleep": "sleep",
            "put my laptop to sleep": "sleep",
        }

        for command, action in cases.items():
            with self.subTest(command=command):
                result = route_local_intent(command)
                self.assertIsNotNone(result)
                self.assertEqual(result["action"], action)

    def test_returns_none_for_complex_commands_that_need_llm(self):
        self.assertIsNone(route_local_intent("open YouTube, start lo-fi, and then start focus mode"))


if __name__ == "__main__":
    unittest.main()
