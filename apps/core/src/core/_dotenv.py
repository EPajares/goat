from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"
ROOT_ENV = Path("/app/.env")

load_dotenv(ENV_FILE)

if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=True)
