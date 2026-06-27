from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "agent-ops"
    environment: str = "test"
    api_prefix: str = "/api"

    database_host: str = "pgm-bp103m50b4w6569h.pg.rds.aliyuncs.com"
    database_port: int = 5432
    database_user: str = "tactile_app"
    database_password: str = ""  # env: DATABASE_PASSWORD
    database_name: str = "tactile"
    database_schema: str = "agent_ops_test"

    jwt_secret: str = "agent-ops-test-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    cors_origins: str = "*"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
