import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.config import Settings
from src.llm.exceptions import (
    GatewayNotConfiguredError,
    GatewayRequestValidationError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    StructuredOutputValidationError,
    UnsupportedModelError,
    UnsupportedProviderError,
    ProviderResponseError,
)
from src.llm.gateway import LLMGateway
from src.llm.contracts import ProviderRequest
from src.llm.provider import DeepSeekChatProvider, OpenAIResponsesProvider, create_provider
from src.main import app


def configured_settings(**overrides):
    values = {
        "db_host": "localhost", "db_name": "test", "db_user": "test", "db_password": "test",
        "llm_gateway_enabled": True, "llm_api_key": SecretStr("top-secret-key"),
        "llm_default_model": "test-model", "llm_allowed_models": "test-model,other-model",
        "llm_max_attempts": 3,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def response_payload(output=None):
    output = output or {"summary": "Observed decline.", "limitations": ["Small sample"], "confidence": 0.8}
    return {
        "id": "resp_test", "status": "completed",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(output)}]}],
        "usage": {"input_tokens": 20, "output_tokens": 10},
    }


class LLMGatewayTestCase(unittest.TestCase):
    def make_gateway(self, handler, **settings_overrides):
        client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://provider.test/v1")
        provider = OpenAIResponsesProvider("top-secret-key", "https://provider.test/v1", 1, client=client)
        gateway = LLMGateway(configured_settings(**settings_overrides), provider=provider, sleep=lambda _: None)
        self.addCleanup(client.close)
        return gateway

    def test_valid_structured_request_and_provenance(self):
        captured = {}
        def handler(request):
            captured["authorization"] = request.headers["authorization"]
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json=response_payload())
        result = self.make_gateway(handler).invoke("evidence_summary_v1", {
            "research_question": "Are observations declining?", "evidence_notes": ["Count fell from 10 to 7"]
        })
        self.assertEqual(result.output["confidence"], 0.8)
        self.assertEqual(result.metadata.provider_request_id, "resp_test")
        self.assertEqual(result.metadata.attempts, 1)
        self.assertEqual(captured["body"]["text"]["format"]["type"], "json_schema")
        self.assertTrue(captured["body"]["text"]["format"]["strict"])
        self.assertEqual(captured["authorization"], "Bearer top-secret-key")
        self.assertNotIn("top-secret-key", repr(result))

    def test_model_allowlist_is_enforced_before_network(self):
        gateway = self.make_gateway(lambda request: self.fail("network called"))
        with self.assertRaises(UnsupportedModelError):
            gateway.invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": ["E"]}, model="unapproved")

    def test_input_and_output_validation(self):
        gateway = self.make_gateway(lambda request: httpx.Response(200, json=response_payload()))
        with self.assertRaises(GatewayRequestValidationError):
            gateway.invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": [], "extra": True})
        invalid = self.make_gateway(lambda request: httpx.Response(200, json=response_payload({"summary": "x", "limitations": [], "confidence": 2.0})))
        with self.assertRaises(StructuredOutputValidationError):
            invalid.invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": ["E"]})

    def test_transient_rate_limit_retries_but_auth_does_not(self):
        calls = []
        def transient(request):
            calls.append(1)
            return httpx.Response(429 if len(calls) < 3 else 200, json=response_payload())
        result = self.make_gateway(transient).invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": ["E"]})
        self.assertEqual(result.metadata.attempts, 3)
        auth_calls = []
        def auth(request):
            auth_calls.append(1)
            return httpx.Response(401, json={"error": "bad key"})
        with self.assertRaises(ProviderAuthenticationError):
            self.make_gateway(auth).invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": ["E"]})
        self.assertEqual(len(auth_calls), 1)

    def test_retries_are_bounded_and_error_does_not_leak_key(self):
        calls = []
        def handler(request):
            calls.append(1)
            return httpx.Response(429, json={})
        with self.assertRaises(ProviderRateLimitError) as caught:
            self.make_gateway(handler).invoke("evidence_summary_v1", {"research_question": "Q", "evidence_notes": ["E"]})
        self.assertEqual(len(calls), 3)
        self.assertNotIn("top-secret-key", str(caught.exception))

    def test_disabled_configuration_and_unknown_provider_fail_closed(self):
        disabled = configured_settings(llm_gateway_enabled=False)
        with self.assertRaises(GatewayNotConfiguredError):
            LLMGateway(disabled)._resolve_provider()
        with self.assertRaises(UnsupportedProviderError):
            create_provider("invented", api_key="x", base_url="https://example.test", timeout_seconds=1)

    def test_health_is_read_only_and_contains_no_secret(self):
        client = TestClient(app)
        response = client.get("/health/llm-gateway")
        self.assertEqual(response.status_code, 200)
        self.assertIn("configured", response.json())
        self.assertNotIn("api_key", response.json())
        self.assertIsInstance(response.json()["api_key_configured"], bool)
        self.assertNotIn("top-secret-key", response.text)
        self.assertEqual(client.post("/llm/generate").status_code, 404)

    def test_deepseek_structured_request_and_response(self):
        captured = {}
        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(200, json={
                "id": "deepseek-test", "choices": [{"finish_reason": "stop", "message": {"content": '{"summary":"ok","limitations":[],"confidence":0.9}'}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            })
        client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.deepseek.test")
        self.addCleanup(client.close)
        provider = DeepSeekChatProvider("secret", "https://api.deepseek.test", 1, client=client)
        result = provider.generate(ProviderRequest(
            model="deepseek-v4-flash", instructions="Return evidence", input_text="Evidence",
            schema_name="evidence", output_schema={"type": "object"}, max_output_tokens=100,
        ))
        self.assertEqual(result.request_id, "deepseek-test")
        self.assertEqual(result.input_tokens, 12)
        self.assertEqual(captured["body"]["thinking"], {"type": "disabled"})
        self.assertEqual(captured["body"]["response_format"], {"type": "json_object"})
        self.assertIn("schema", captured["body"]["messages"][0]["content"].lower())

    def test_deepseek_rejects_empty_or_truncated_output(self):
        for finish_reason, content in (("stop", ""), ("length", "{}")):
            client = httpx.Client(transport=httpx.MockTransport(lambda request, f=finish_reason, c=content: httpx.Response(200, json={
                "id": "x", "choices": [{"finish_reason": f, "message": {"content": c}}], "usage": {},
            })), base_url="https://api.deepseek.test")
            self.addCleanup(client.close)
            provider = DeepSeekChatProvider("secret", "https://api.deepseek.test", 1, client=client)
            with self.assertRaises(ProviderResponseError):
                provider.generate(ProviderRequest(model="deepseek-v4-flash", instructions="x", input_text="x", schema_name="x", output_schema={}, max_output_tokens=10))

    def test_diagnostic_endpoint_hides_key_and_balance_amounts(self):
        class FakeDeepSeek:
            def check_balance(self):
                return {"is_available": True, "balance_infos": [{"currency": "USD", "total_balance": "123.45", "granted_balance": "1", "topped_up_balance": "122.45"}]}
            def close(self):
                pass
        client = TestClient(app)
        with patch("src.routers.llm_gateway.create_provider", return_value=FakeDeepSeek()), \
             patch("src.routers.llm_gateway.settings.llm_show_balance_amounts", False):
            response = client.post("/llm-gateway/test-connection")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["quota_available"])
        self.assertEqual(payload["balances"], [{"currency": "USD", "total_balance": None, "granted_balance": None, "topped_up_balance": None}])
        self.assertNotIn("123.45", response.text)
        self.assertNotIn("api_key", response.text)


if __name__ == "__main__":
    unittest.main()
