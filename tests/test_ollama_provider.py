import unittest
from unittest.mock import MagicMock, patch

from ultron.providers.base import ProviderRequest
from ultron.providers.ollama import OllamaProvider


def _mock_response(status_code=200, json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


class OllamaProviderTests(unittest.TestCase):
    def test_disabled_without_base_url(self):
        provider = OllamaProvider(base_url="")

        self.assertFalse(provider.enabled)
        response = provider.analyze(ProviderRequest(command="open chrome"))

        self.assertEqual(response.status, "unavailable")
        self.assertEqual(response.error, "local_llm_not_configured")

    @patch("ultron.providers.ollama.requests.post")
    def test_analyze_returns_action_on_success(self, mock_post):
        mock_post.return_value = _mock_response(
            200,
            json_data={"message": {"content": '{"action": "open_app", "params": {"app": "chrome"}, "response": "Opening Chrome."}'}},
        )
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:1b")

        response = provider.analyze(ProviderRequest(command="open chrome"))

        self.assertTrue(response.ok)
        self.assertEqual(response.action["action"], "open_app")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["model"], "llama3.2:1b")

    @patch("ultron.providers.ollama.requests.post")
    def test_analyze_reports_http_error(self, mock_post):
        mock_post.return_value = _mock_response(500)
        provider = OllamaProvider(base_url="http://localhost:11434")

        response = provider.analyze(ProviderRequest(command="open chrome"))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.error, "http_500")

    @patch("ultron.providers.ollama.requests.post")
    def test_analyze_reports_unparseable_response(self, mock_post):
        mock_post.return_value = _mock_response(200, json_data={"message": {"content": "not json at all"}})
        provider = OllamaProvider(base_url="http://localhost:11434")

        response = provider.analyze(ProviderRequest(command="open chrome"))

        self.assertEqual(response.status, "error")
        self.assertEqual(response.error, "unparseable_response")


if __name__ == "__main__":
    unittest.main()
