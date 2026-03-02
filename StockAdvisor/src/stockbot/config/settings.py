from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file = ".env", extra = "ignore")

    saxo_access_token: str = Field(..., env="SAXO_ACCESS_TOKEN")
    saxo_env: str = Field(..., env="SAXO_ENV")
    fmp_api_key: str = Field(..., env="FMP_API_KEY")

    @property
    def saxo_base_url(self) -> str:
        if self.saxo_env.upper() == "SIM":
            return "https://gateway.saxobank.com/sim/openapi"
        return "https://gateway.saxobank.com/openapi"


settings = Settings()
