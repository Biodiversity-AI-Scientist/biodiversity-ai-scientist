import os
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pydantic import SecretStr

from src.config import settings

router = APIRouter(prefix="/config", tags=["configuration"])


class UpdateLLMConfigRequest(BaseModel):
    enabled: bool = Field(default=True, description="Enable or disable LLM Gateway")
    provider: str = Field(default="openai_responses", description="Provider ID (openai_responses, deepseek_chat, ollama)")
    base_url: str = Field(default="https://api.openai.com/v1", description="API Base URL")
    api_key: Optional[str] = Field(default=None, description="API Key")
    default_model: str = Field(default="gpt-4o", description="Default model name")
    allowed_models: Optional[str] = Field(default=None, description="Comma-separated allowed models")


@router.post("/llm", status_code=status.HTTP_200_OK)
def update_llm_config_endpoint(req: UpdateLLMConfigRequest) -> Dict[str, Any]:
    """
    Safely updates LLM Gateway configuration in the local .env file.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    env_path = repo_root / ".env"

    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()

    # Dictionary of existing variables
    new_vars = {
        "LLM_GATEWAY_ENABLED": "true" if req.enabled else "false",
        "LLM_PROVIDER": req.provider.strip(),
        "LLM_BASE_URL": req.base_url.strip(),
        "LLM_DEFAULT_MODEL": req.default_model.strip(),
        "LLM_ALLOWED_MODELS": (req.allowed_models or req.default_model).strip(),
    }

    if req.api_key is not None:
        new_vars["LLM_API_KEY"] = req.api_key.strip()

    # Update existing lines or append
    updated_keys = set()
    output_lines = []
    for line in env_lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            output_lines.append(line)
            continue
        key, _, _ = line.partition("=")
        key = key.strip()
        if key in new_vars:
            output_lines.append(f"{key}={new_vars[key]}")
            updated_keys.add(key)
        else:
            output_lines.append(line)

    # Append any new variables that weren't present
    for k, v in new_vars.items():
        if k not in updated_keys:
            output_lines.append(f"{k}={v}")

    # Write updated .env
    env_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    # Update in-memory settings
    settings.llm_gateway_enabled = req.enabled
    settings.llm_provider = req.provider.strip()
    settings.llm_base_url = req.base_url.strip()
    settings.llm_default_model = req.default_model.strip()
    settings.llm_allowed_models = (req.allowed_models or req.default_model).strip()
    if req.api_key is not None:
        settings.llm_api_key = SecretStr(req.api_key.strip()) if req.api_key.strip() else None

    return {
        "success": True,
        "message": "LLM Gateway configuration updated successfully in .env.",
        "configured": settings.llm_configured,
        "provider": settings.llm_provider,
        "default_model": settings.llm_default_model,
    }
