from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All fields are immutable after construction (frozen=True).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
    )

    ANTHROPIC_API_KEY: str
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    TAVILY_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"
    PLANNING_MODEL: str = "claude-sonnet-4-20250514"
    TASK_MODEL: str = "claude-sonnet-4-20250514"
    MAX_ITERATIONS: int = 50
    MAX_TOKENS: int = 8192
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SANDBOX_PROVIDER: str = "boxlite"  # "boxlite" or "e2b"
    E2B_API_KEY: str = ""
    API_KEY: str = ""  # Optional API key for authentication; empty = allow all
    RATE_LIMIT_PER_MINUTE: int = 30
    DEFAULT_SYSTEM_PROMPT: str = (
        "You are a helpful AI assistant with access to a sandboxed coding environment. "
        "You can write and execute code (Python, JavaScript, Bash), manage files, "
        "install packages, and run shell commands inside a secure sandbox.\n\n"
        "When the user asks you to build something (e.g., an app, script, or project):\n"
        "1. Use file_write to create the necessary files in /workspace\n"
        "2. Use shell_exec or code_run to run and test the code\n"
        "3. Use package_install to install any required dependencies\n"
        "4. Use message_user to share results and explanations with the user\n\n"
        "Always write real, working code. Execute it to verify it works before "
        "presenting results. Think step by step."
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, immutable Settings instance."""
    return Settings()
