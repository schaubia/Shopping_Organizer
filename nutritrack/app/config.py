from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database — SQLite for dev, PostgreSQL for prod
    DATABASE_URL: str = "sqlite:///./nutritrack.db"

    # USDA FoodData Central
    USDA_API_KEY: str = "DEMO_KEY"
    USDA_SEARCH_URL: str = "https://api.nal.usda.gov/fdc/v1/foods/search"
    USDA_FOOD_URL: str = "https://api.nal.usda.gov/fdc/v1/food"

    # JWT Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    # Stripe (payments — fill in when ready)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
