class LLMGatewayError(Exception):
    """Base exception with a stable, non-secret error code."""
    code = "llm_gateway_error"
    retryable = False

class GatewayNotConfiguredError(LLMGatewayError): code = "gateway_not_configured"
class UnsupportedProviderError(LLMGatewayError): code = "unsupported_provider"
class UnsupportedModelError(LLMGatewayError): code = "unsupported_model"
class GatewayRequestValidationError(LLMGatewayError): code = "request_validation_failed"
class ProviderAuthenticationError(LLMGatewayError): code = "provider_authentication_failed"
class ProviderRateLimitError(LLMGatewayError):
    code = "provider_rate_limited"
    retryable = True
class ProviderTimeoutError(LLMGatewayError):
    code = "provider_timeout"
    retryable = True
class ProviderUnavailableError(LLMGatewayError):
    code = "provider_unavailable"
    retryable = True
class ProviderResponseError(LLMGatewayError): code = "provider_response_invalid"
class StructuredOutputValidationError(LLMGatewayError): code = "structured_output_invalid"
