from pydantic import BaseModel, ConfigDict


class GatewayStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    enabled: bool
    configured: bool
    provider: str
    default_model: str | None
    allowed_model_count: int
    api_key_configured: bool


class BalanceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: str
    total_balance: str | None = None
    granted_balance: str | None = None
    topped_up_balance: str | None = None


class GatewayDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    authenticated: bool
    quota_available: bool
    provider: str
    model: str
    checked_at: str
    balances: list[BalanceInfo]
    balance_amounts_visible: bool
