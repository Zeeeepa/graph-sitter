from graph_sitter.configs.models.base_config import BaseConfig


class SecretsConfig(BaseConfig):
    """Configuration for various API secrets and tokens.

    Loads from environment variables.
    Falls back to .env file for missing values.
    """

    def __init__(self, prefix: str = "", *args, **kwargs) -> None:
        # Pass prefix directly to BaseConfig
        super().__init__(prefix, *args, **kwargs)

    github_token: str | None = None
    openai_api_key: str | None = None
    linear_api_key: str | None = None
    
    # Enhanced Codegen SDK configuration
    codegen_org_id: str | None = None
    codegen_token: str | None = None
    codegen_base_url: str | None = None
