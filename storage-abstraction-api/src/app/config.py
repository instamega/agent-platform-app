from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    app_port: int = 8080
    app_log_level: str = "INFO"
    api_key: str = "changeme"

    vector_backend: str = "pgvector"
    chat_backend: str = "postgres"
    graph_backend: str = "neo4j"

    pg_dsn: str = "postgresql+asyncpg://storage:storage@localhost:5432/storage"
    n4j_uri: str = "bolt://localhost:7687"
    n4j_user: str = "neo4j"
    n4j_pass: str = "neo4j_password"

    class Config:
        env_file = ".env"

settings = Settings()