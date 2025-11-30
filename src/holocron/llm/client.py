"""LLM client wrapper for Holocron.

This module provides a unified interface to multiple LLM providers
using LiteLLM, with retry logic and token counting support.

Supported providers:
- Anthropic (Claude)
- OpenAI (GPT-4)
- Google (Gemini)
"""

from dataclasses import dataclass
from typing import Any, Callable

import litellm
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from holocron.config import get_settings


@dataclass
class LLMResponse:
    """Response from an LLM call.

    Attributes:
        content: The response text
        model: The model that generated the response
        usage: Token usage information
        raw_response: The full response object
    """

    content: str
    model: str
    usage: dict[str, int]
    raw_response: Any = None


class LLMClient:
    """Unified LLM client using LiteLLM.

    Provides a consistent interface to multiple LLM providers with
    automatic retry logic and token counting.

    Example:
        ```python
        client = LLMClient()

        response = client.complete(
            system_prompt="You are a helpful tutor.",
            user_message="Explain list comprehensions.",
        )

        print(response.content)
        ```
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int = 3,
    ) -> None:
        """Initialize the LLM client.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-sonnet")
            temperature: Sampling temperature (0-1)
            max_retries: Maximum retry attempts for failed requests
        """
        settings = get_settings()

        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else settings.temperature
        self.max_retries = max_retries

        # Configure API keys from settings
        self._configure_api_keys(settings)

    def _configure_api_keys(self, settings) -> None:
        """Configure API keys for LiteLLM."""
        import os

        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

    @retry(
        retry=retry_if_exception_type((litellm.RateLimitError, litellm.APIConnectionError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
    )
    def complete(
        self,
        user_message: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            user_message: The user's input message
            system_prompt: Optional system prompt
            model: Override the default model
            temperature: Override the default temperature
            max_tokens: Maximum tokens in response

        Returns:
            LLMResponse with the generated content
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_message})

        response = litellm.completion(
            model=model or self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response,
        )

    def complete_with_callback(
        self,
        user_message: str,
        system_prompt: str | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> LLMResponse:
        """Generate a completion with optional streaming callback.

        Args:
            user_message: The user's input message
            system_prompt: Optional system prompt
            callback: Optional callback for streaming chunks

        Returns:
            LLMResponse with the generated content
        """
        if callback is None:
            return self.complete(user_message, system_prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = litellm.completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=True,
        )

        full_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                callback(content)

        return LLMResponse(
            content=full_content,
            model=self.model,
            usage={"total_tokens": 0},  # Streaming doesn't return usage
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Approximate token count
        """
        try:
            import tiktoken

            # Use cl100k_base encoding (used by GPT-4, Claude)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate of 4 characters per token
            return len(text) // 4

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for a completion.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Approximate costs per 1K tokens (varies by model)
        costs = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0005, 0.0015),
            "claude-3-opus": (0.015, 0.075),
            "claude-3-sonnet": (0.003, 0.015),
            "claude-3-haiku": (0.00025, 0.00125),
            "gemini-pro": (0.00025, 0.0005),
        }

        # Find matching cost tier
        for model_prefix, (input_cost, output_cost) in costs.items():
            if model_prefix in self.model.lower():
                return (
                    prompt_tokens / 1000 * input_cost
                    + completion_tokens / 1000 * output_cost
                )

        # Default estimate
        return (prompt_tokens + completion_tokens) / 1000 * 0.01


# Convenience function for quick completions
def quick_complete(
    user_message: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> str:
    """Quick completion without creating a client instance.

    Args:
        user_message: The user's input
        system_prompt: Optional system prompt
        model: Optional model override

    Returns:
        The response content string
    """
    client = LLMClient(model=model)
    response = client.complete(user_message, system_prompt)
    return response.content
