import unittest
from unittest.mock import MagicMock, patch

from ultron.providers.gemini import GeminiProvider


def _mock_response(status_code=200, text="", json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.json.return_value = json_data or {}
    return response


class GeminiProviderTests(unittest.TestCase):
    def test_disabled_without_api_key(self):
        provider = GeminiProvider(api_key="")

        self.assertFalse(provider.enabled)
        response = provider.describe_image(b"fake-png-bytes")

        self.assertEqual(response.status, "error")
        self.assertEqual(response.error, "missing_api_key")

    @patch("ultron.providers.gemini.requests.post")
    def test_describe_image_returns_text_on_success(self, mock_post):
        mock_post.return_value = _mock_response(
            200,
            json_data={"candidates": [{"content": {"parts": [{"text": "A code editor is open."}]}}]},
        )
        provider = GeminiProvider(api_key="test-key")

        response = provider.describe_image(b"fake-png-bytes")

        self.assertTrue(response.ok)
        self.assertEqual(response.text, "A code editor is open.")
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["params"], {"key": "test-key"})

    @patch("ultron.providers.gemini.requests.post")
    def test_describe_image_reports_http_error(self, mock_post):
        mock_post.return_value = _mock_response(429, text="rate limited")
        provider = GeminiProvider(api_key="test-key")

        response = provider.describe_image(b"fake-png-bytes")

        self.assertEqual(response.status, "error")
        self.assertIn("http_429", response.error)

    @patch("ultron.providers.gemini.requests.post")
    def test_describe_image_reports_unparseable_response(self, mock_post):
        mock_post.return_value = _mock_response(200, json_data={"unexpected": "shape"})
        provider = GeminiProvider(api_key="test-key")

        response = provider.describe_image(b"fake-png-bytes")

        self.assertEqual(response.status, "error")
        self.assertEqual(response.error, "unparseable_response")

    @patch("ultron.providers.gemini.requests.post")
    def test_custom_question_is_sent_as_prompt(self, mock_post):
        mock_post.return_value = _mock_response(
            200,
            json_data={"candidates": [{"content": {"parts": [{"text": "Yes, a red icon."}]}}]},
        )
        provider = GeminiProvider(api_key="test-key")

        provider.describe_image(b"fake-png-bytes", question="Is there a red icon?")

        _, kwargs = mock_post.call_args
        prompt = kwargs["json"]["contents"][0]["parts"][0]["text"]
        self.assertEqual(prompt, "Is there a red icon?")


if __name__ == "__main__":
    unittest.main()
