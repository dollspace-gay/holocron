"""Tests for LLM client module."""

from unittest.mock import MagicMock, patch

import pytest

from holocron.llm import LLMClient, LLMResponse, quick_complete


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_response(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Test content",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

        assert response.content == "Test content"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 30
        assert response.raw_response is None

    def test_response_with_raw(self):
        """Test creating a response with raw response object."""
        raw = {"id": "test-123", "choices": []}
        response = LLMResponse(
            content="Test",
            model="claude-3-sonnet",
            usage={"total_tokens": 50},
            raw_response=raw,
        )

        assert response.raw_response == raw


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_init_default_settings(self):
        """Test client initialization with default settings."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()

            assert client.model == "gpt-4"
            assert client.temperature == 0.7
            assert client.max_retries == 3

    def test_init_custom_settings(self):
        """Test client initialization with custom settings."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient(
                model="claude-3-opus",
                temperature=0.3,
                max_retries=5,
            )

            assert client.model == "claude-3-opus"
            assert client.temperature == 0.3
            assert client.max_retries == 5

    def test_count_tokens_with_tiktoken(self):
        """Test token counting with tiktoken."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            count = client.count_tokens("Hello, world!")

            # Token count should be reasonable
            assert count > 0
            assert count < 10  # Short text shouldn't have many tokens

    def test_count_tokens_fallback(self):
        """Test token counting fallback when tiktoken fails."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()

            # Patch tiktoken to raise an error
            with patch("tiktoken.get_encoding", side_effect=Exception("No tiktoken")):
                text = "Hello, world! This is a test."
                count = client.count_tokens(text)

                # Fallback uses ~4 chars per token
                assert count == len(text) // 4

    def test_estimate_cost_gpt4(self):
        """Test cost estimation for GPT-4."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            cost = client.estimate_cost(1000, 500)

            # GPT-4: $0.03/1K input, $0.06/1K output
            expected = 1000 / 1000 * 0.03 + 500 / 1000 * 0.06
            assert cost == expected

    def test_estimate_cost_claude(self):
        """Test cost estimation for Claude."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="claude-3-sonnet",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            cost = client.estimate_cost(1000, 500)

            # Claude-3-sonnet: $0.003/1K input, $0.015/1K output
            expected = 1000 / 1000 * 0.003 + 500 / 1000 * 0.015
            assert cost == expected

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation for unknown model."""
        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="unknown-model-x",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            cost = client.estimate_cost(1000, 500)

            # Default: $0.01/1K total
            expected = (1000 + 500) / 1000 * 0.01
            assert cost == expected

    @patch("holocron.llm.client.litellm")
    def test_complete_success(self, mock_litellm):
        """Test successful completion."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is the response"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_litellm.completion.return_value = mock_response

        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            result = client.complete(
                user_message="Hello",
                system_prompt="You are helpful",
            )

            assert result.content == "This is the response"
            assert result.model == "gpt-4"
            assert result.usage["total_tokens"] == 30

            # Verify the call was made correctly
            mock_litellm.completion.assert_called_once()
            call_args = mock_litellm.completion.call_args
            assert call_args.kwargs["model"] == "gpt-4"
            assert len(call_args.kwargs["messages"]) == 2
            assert call_args.kwargs["messages"][0]["role"] == "system"
            assert call_args.kwargs["messages"][1]["role"] == "user"

    @patch("holocron.llm.client.litellm")
    def test_complete_without_system_prompt(self, mock_litellm):
        """Test completion without system prompt."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15
        mock_litellm.completion.return_value = mock_response

        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            result = client.complete(user_message="Hello")

            call_args = mock_litellm.completion.call_args
            # Should only have user message, no system prompt
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["role"] == "user"

    @patch("holocron.llm.client.litellm")
    def test_complete_with_callback_no_callback(self, mock_litellm):
        """Test complete_with_callback without callback falls back to complete."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15
        mock_litellm.completion.return_value = mock_response

        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            result = client.complete_with_callback(
                user_message="Hello",
                callback=None,
            )

            assert result.content == "Response"

    @patch("holocron.llm.client.litellm")
    def test_complete_with_streaming_callback(self, mock_litellm):
        """Test streaming completion with callback."""
        # Mock streaming response
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello "

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "World"

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = None  # End of stream

        mock_litellm.completion.return_value = iter([chunk1, chunk2, chunk3])

        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            client = LLMClient()
            chunks_received = []
            result = client.complete_with_callback(
                user_message="Hello",
                callback=lambda x: chunks_received.append(x),
            )

            assert result.content == "Hello World"
            assert chunks_received == ["Hello ", "World"]
            assert result.usage["total_tokens"] == 0  # Streaming doesn't return usage


class TestQuickComplete:
    """Tests for quick_complete convenience function."""

    @patch("holocron.llm.client.litellm")
    def test_quick_complete(self, mock_litellm):
        """Test quick_complete function."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Quick response"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15
        mock_litellm.completion.return_value = mock_response

        with patch("holocron.llm.client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                default_model="gpt-4",
                temperature=0.7,
                anthropic_api_key=None,
                openai_api_key=None,
                gemini_api_key=None,
            )

            result = quick_complete("Hello")

            assert result == "Quick response"
