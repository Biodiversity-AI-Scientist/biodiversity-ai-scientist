import json
from collections.abc import Callable
from typing import Any, Protocol

import httpx

from src.llm.contracts import ProviderRequest, ProviderResponse
from src.llm.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    UnsupportedProviderError,
)


def _raise_for_provider_error(response: httpx.Response) -> None:
    if response.status_code in (401, 403):
        raise ProviderAuthenticationError("Provider rejected credentials")
    if response.status_code == 429:
        raise ProviderRateLimitError("Provider rate limit reached")
    if response.status_code >= 500:
        raise ProviderUnavailableError("Provider is unavailable")
    if response.status_code >= 400:
        raise ProviderResponseError("Provider rejected the request")


class LLMProvider(Protocol):
    provider_id: str
    def generate(self, request: ProviderRequest) -> ProviderResponse: ...
    def close(self) -> None: ...


class BaseHTTPProvider:
    def __init__(self, api_key: str, base_url: str, timeout_seconds: float, client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _post(self, endpoint: str, payload: dict[str, Any]) -> httpx.Response:
        try:
            response = self._client.post(endpoint, headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}, json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Provider request timed out") from exc
        except httpx.TransportError as exc:
            raise ProviderUnavailableError("Provider transport failed") from exc
        _raise_for_provider_error(response)
        return response


class OpenAIResponsesProvider(BaseHTTPProvider):
    provider_id = "openai_responses"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        response = self._post("/responses", {
            "model": request.model, "instructions": request.instructions, "input": request.input_text,
            "max_output_tokens": request.max_output_tokens,
            "text": {"format": {"type": "json_schema", "name": request.schema_name, "strict": True, "schema": request.output_schema}},
        })
        try:
            payload = response.json()
            output_text = next(content["text"] for item in payload["output"] if item.get("type") == "message" for content in item.get("content", []) if content.get("type") == "output_text")
            usage = payload.get("usage") or {}
            return ProviderResponse(request_id=payload["id"], status=payload["status"], output_text=output_text, input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"))
        except (KeyError, StopIteration, TypeError, ValueError) as exc:
            raise ProviderResponseError("Provider response was malformed") from exc


class DeepSeekChatProvider(BaseHTTPProvider):
    provider_id = "deepseek_chat"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        schema_json = json.dumps(request.output_schema, separators=(",", ":"))
        response = self._post("/chat/completions", {
            "model": request.model,
            "messages": [
                {"role": "system", "content": f"{request.instructions}\nReturn JSON matching this schema exactly: {schema_json}"},
                {"role": "user", "content": request.input_text},
            ],
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "max_tokens": request.max_output_tokens,
            "stream": False,
        })
        try:
            payload = response.json()
            choice = payload["choices"][0]
            output_text = choice["message"]["content"]
            if not isinstance(output_text, str) or not output_text.strip():
                raise ValueError("empty content")
            if choice.get("finish_reason") != "stop":
                raise ValueError("incomplete content")
            usage = payload.get("usage") or {}
            return ProviderResponse(request_id=payload["id"], status="completed", output_text=output_text, input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderResponseError("Provider response was malformed or incomplete") from exc

    def check_balance(self) -> dict[str, Any]:
        try:
            response = self._client.get("/user/balance", headers={"Authorization": f"Bearer {self._api_key}", "Accept": "application/json"})
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Provider request timed out") from exc
        except httpx.TransportError as exc:
            raise ProviderUnavailableError("Provider transport failed") from exc
        _raise_for_provider_error(response)
        try:
            payload = response.json()
            balances = payload["balance_infos"]
            if not isinstance(balances, list):
                raise ValueError("invalid balances")
            return {"is_available": bool(payload["is_available"]), "balance_infos": balances}
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderResponseError("Provider balance response was malformed") from exc


ProviderFactory = Callable[..., LLMProvider]
PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    OpenAIResponsesProvider.provider_id: OpenAIResponsesProvider,
    DeepSeekChatProvider.provider_id: DeepSeekChatProvider,
}


def create_provider(provider_id: str, **kwargs: Any) -> LLMProvider:
    try:
        return PROVIDER_FACTORIES[provider_id](**kwargs)
    except KeyError as exc:
        raise UnsupportedProviderError("Configured provider is not supported") from exc
