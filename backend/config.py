import os
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()

class Settings(BaseModel):
    supabase_url: str
    supabase_key: str
    openai_model: str = "gpt-5-nano"
    default_expiry_hours: int = 23
    max_radius_meters: int = 5000


def load_settings() -> Settings:
    return Settings(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-nano"),
        default_expiry_hours=int(os.getenv("DEFAULT_EXPIRY_HOURS", "23")),
        max_radius_meters=int(os.getenv("MAX_RADIUS_METERS", "5000")),
    )

def validate_settings(settings: Settings) -> None:
    if not settings.supabase_url:
        raise RuntimeError("Missing SUPABASE_URL")
    if not settings.supabase_key:
        raise RuntimeError("Missing SUPABASE_KEY")


settings = load_settings()
