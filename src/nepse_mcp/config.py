from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nepalipaisa_base_url: str = "https://nepalipaisa.com/api"
    nepse_http_timeout: int = 10
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
