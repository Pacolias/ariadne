from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ariadne-dev-password"

    qdrant_url: str = "http://localhost:6333"

    # Reasoning (Phase 3) — grounded synthesis, zero hallucination tolerance.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    # Bulk/cheap extraction (Phase 1) — CTI entity extraction, SBOM/IaC parsing assistance.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"
    embedding_size: int = 768

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
