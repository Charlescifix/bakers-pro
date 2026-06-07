from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://bakerprofit:bakerprofit@localhost:5432/bakerprofit"

    # Comma-separated origins, e.g.:
    # CORS_ORIGINS=https://main.xxxx.amplifyapp.com,http://localhost:5173
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173,http://localhost:3000"

    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MAX_UPLOAD_SIZE_MB: int = 20

    DEFAULT_COUNTRY_CODE: str = "GB"
    DEFAULT_CURRENCY: str = "GBP"
    DEFAULT_TIMEZONE: str = "Europe/London"
    DEFAULT_LABOUR_RATE_PER_HOUR: str = "10.00"
    DEFAULT_DESIRED_MARGIN_PERCENT: str = "60.00"
    DEFAULT_FOOD_COST_TARGET_PERCENT: str = "35.00"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
