import os
from pathlib import Path

# Load .env manually if it exists to populate os.environ
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Split key/value
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key_change_me_in_production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./project.db")

settings = Settings()
