import hashlib, json, logging, time, uuid
from collections.abc import Callable
from typing import Any
from pydantic import ValidationError
from src.config import Settings, settings
from src.llm.contracts import GatewayResult, InvocationMetadata, ProviderRequest
from src.llm.exceptions import GatewayNotConfiguredError, GatewayRequestValidationError, LLMGatewayError, StructuredOutputValidationError, UnsupportedModelError
from src.llm.provider import LLMProvider, create_provider
from src.llm.registry import get_template

logger = logging.getLogger(__name__)

class LLMGateway:
    def __init__(self, config: Settings = settings, provider: LLMProvider | None = None, sleep: Callable[[float], None] = time.sleep) -> None:
        self.config, self._provider, self._sleep = config, provider, sleep

    def _resolve_provider(self) -> LLMProvider:
        if not self.config.llm_configured:
            raise GatewayNotConfiguredError("LLM gateway is not configured")
        if self._provider is not None:
            return self._provider
        return create_provider(self.config.llm_provider, api_key=self.config.llm_api_key.get_secret_value(), base_url=self.config.llm_base_url, timeout_seconds=self.config.llm_timeout_seconds)

    def invoke(self, template_id: str, inputs: dict[str, Any], model: str | None = None) -> GatewayResult:
        selected_model = model or self.config.llm_default_model
        if not selected_model or selected_model not in self.config.allowed_llm_models:
            raise UnsupportedModelError("Model is not in the configured allowlist")
        template = get_template(template_id)
        try:
            validated_inputs = template.input_model.model_validate(inputs)
        except ValidationError as exc:
            raise GatewayRequestValidationError("Prompt inputs are invalid") from exc
        prompt = template.render(validated_inputs)
        request = ProviderRequest(model=selected_model, instructions=template.instructions, input_text=prompt, schema_name=template.template_id, output_schema=template.output_model.model_json_schema(), max_output_tokens=self.config.llm_max_output_tokens)
        provider = self._resolve_provider()
        invocation_id, started, attempts = str(uuid.uuid4()), time.monotonic(), 0
        try:
            while True:
                attempts += 1
                try:
                    response = provider.generate(request)
                    break
                except LLMGatewayError as exc:
                    if not exc.retryable or attempts >= self.config.llm_max_attempts:
                        logger.warning("llm_invocation_failed invocation_id=%s provider=%s model=%s template=%s error_code=%s attempts=%s", invocation_id, self.config.llm_provider, selected_model, template_id, exc.code, attempts)
                        raise
                    self._sleep(min(0.25 * (2 ** (attempts - 1)), 2.0))
            try:
                from src.llm.json_repair import repair_and_parse_json
                raw_json = repair_and_parse_json(response.output_text)
                validated_output = template.output_model.model_validate(raw_json)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                logger.error("Structured output validation failed for template %s: %s | Output text: %.300s", template_id, exc, response.output_text)
                raise StructuredOutputValidationError(f"Model output failed schema validation: {exc}") from exc


            latency_ms = round((time.monotonic() - started) * 1000)
            logger.info("llm_invocation_completed invocation_id=%s provider=%s model=%s template=%s latency_ms=%s attempts=%s input_tokens=%s output_tokens=%s", invocation_id, self.config.llm_provider, selected_model, template_id, latency_ms, attempts, response.input_tokens, response.output_tokens)
            return GatewayResult(output=validated_output.model_dump(), metadata=InvocationMetadata(
                invocation_id=invocation_id, provider=self.config.llm_provider, model=selected_model,
                template_id=template_id, schema_id=template.template_id, provider_request_id=response.request_id,
                provider_status=response.status, attempts=attempts, latency_ms=latency_ms,
                input_tokens=response.input_tokens, output_tokens=response.output_tokens,
                prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), response_sha256=hashlib.sha256(response.output_text.encode()).hexdigest(),
            ))
        finally:
            if self._provider is None: provider.close()
