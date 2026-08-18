from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Primary application database (ai_scientist)
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "ai_scientist"
    db_user: str = "ubuntu"
    db_password: str = "ubuntu"

    # External Data Warehouse (DWH) database
    dwh_db_host: str = "localhost"
    dwh_db_port: int = 3306
    dwh_db_name: str = "DWH"
    dwh_db_user: str = "readonly_user"
    dwh_db_password: str = "ubuntu"

    # External Data Lake database
    datalake_db_host: str = "localhost"
    datalake_db_port: int = 3306
    datalake_db_name: str = "DataLake"
    datalake_db_user: str = "readonly_user"
    datalake_db_password: str = "ubuntu"

    # Optional External Service URLs
    papers_api_url: str = ""
    findshell_blog_url: str = ""

    # LLM Gateway Configuration
    llm_gateway_enabled: bool = False
    llm_provider: str = "openai_responses"
    llm_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_default_model: str | None = None
    llm_allowed_models: str = ""
    llm_timeout_seconds: float = 120.0
    llm_max_output_tokens: int = 8000
    llm_max_attempts: int = 3
    llm_show_balance_amounts: bool = False


    @property
    def allowed_llm_models(self) -> frozenset[str]:
        return frozenset(model.strip() for model in self.llm_allowed_models.split(",") if model.strip())

    @property
    def llm_configured(self) -> bool:
        return bool(
            self.llm_gateway_enabled
            and self.llm_api_key
            and self.llm_default_model
            and self.llm_default_model in self.allowed_llm_models
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
