"""
Módulo de configuração do SIGAAS Backend via Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "SIGAAS API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Banco de Dados
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gestao_salas"
    POSTGRES_USER: str = "gestao_salas"
    POSTGRES_PASSWORD: str = "changeme_local_only"
    DATABASE_URL: str = "postgresql://gestao_salas:changeme_local_only@localhost:5432/gestao_salas"
    
    # JWT
    SECRET_KEY: str = "super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()
