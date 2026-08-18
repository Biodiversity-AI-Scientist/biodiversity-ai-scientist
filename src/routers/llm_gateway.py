from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.config import settings
from src.llm.exceptions import LLMGatewayError
from src.llm.provider import DeepSeekChatProvider, create_provider
from src.schemas.llm_gateway import BalanceInfo, GatewayDiagnostic, GatewayStatus

router = APIRouter(prefix="/llm-gateway", tags=["llm-gateway"])


def gateway_status_payload() -> GatewayStatus:
    return GatewayStatus(
        status="ok" if settings.llm_configured else "not_configured",
        enabled=settings.llm_gateway_enabled,
        configured=settings.llm_configured,
        provider=settings.llm_provider,
        default_model=settings.llm_default_model,
        allowed_model_count=len(settings.allowed_llm_models),
        api_key_configured=settings.llm_api_key is not None,
    )


@router.get("/status", response_model=GatewayStatus)
def llm_gateway_status() -> GatewayStatus:
    return gateway_status_payload()


@router.post("/test-connection", response_model=GatewayDiagnostic)
def test_llm_gateway_connection() -> GatewayDiagnostic:
    if not settings.llm_configured:
        raise HTTPException(status_code=503, detail="LLM gateway is not configured")
    if settings.llm_provider != DeepSeekChatProvider.provider_id:
        raise HTTPException(status_code=422, detail="Connection diagnostics are not supported for this provider")
    provider = create_provider(
        settings.llm_provider,
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    try:
        result = provider.check_balance()
    except LLMGatewayError as exc:
        raise HTTPException(status_code=503, detail=f"Connection test failed: {exc.code}") from exc
    finally:
        provider.close()
    balances = []
    for item in result["balance_infos"]:
        values = {"currency": str(item.get("currency") or "")}
        if settings.llm_show_balance_amounts:
            values.update(
                total_balance=str(item.get("total_balance") or ""),
                granted_balance=str(item.get("granted_balance") or ""),
                topped_up_balance=str(item.get("topped_up_balance") or ""),
            )
        balances.append(BalanceInfo(**values))
    return GatewayDiagnostic(
        status="ok", authenticated=True, quota_available=result["is_available"],
        provider=settings.llm_provider, model=settings.llm_default_model,
        checked_at=datetime.now(timezone.utc).isoformat(), balances=balances,
        balance_amounts_visible=settings.llm_show_balance_amounts,
    )
