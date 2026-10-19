from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PROMETHEUS — F.O.G.O."
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Security & JWT
    SECRET_KEY: str = "prometheus_fogo_super_secret_key_hackathon_dsin_2026_jwt_token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite:///./prometheus.db"

    # Default Admin
    DEFAULT_ADMIN_NAME: str = "Administrador PROMETHEUS"
    DEFAULT_ADMIN_EMAIL: str = "admin@prometheus.gov"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
