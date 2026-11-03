from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # pasta "backend"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gestao_financeira"

    jwt_secret: str = "troque-esta-chave"
    jwt_expira_minutos: int = 480

    ollama_url: str = "http://localhost:11434"
    nuextract_modelo: str = "numind/nuextract3:Q4_K_M"
    nuextract_timeout_segundos: int = 180

    pasta_uploads: str = "uploads"
    tamanho_max_upload_mb: int = 10

    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def uploads_path(self) -> Path:
        caminho = Path(self.pasta_uploads)
        return caminho if caminho.is_absolute() else BASE_DIR / caminho


@lru_cache
def get_settings() -> Settings:
    return Settings()
