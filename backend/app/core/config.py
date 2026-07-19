from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    google_client_id: str | None = None
    google_client_secret: str | None = None

    exercisedb_api_key: str | None = None
    exercisedb_api_host: str = "edb-with-videos-and-images-by-ascendapi.p.rapidapi.com"
    exercisedb_base_url: str = "https://edb-with-videos-and-images-by-ascendapi.p.rapidapi.com/api/v1"


settings = Settings()
