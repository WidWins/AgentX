import os
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
PORT_FROM_PLATFORM = os.getenv("PORT", "").strip()
default_host = "0.0.0.0" if PORT_FROM_PLATFORM else "127.0.0.1"
FLASK_HOST = os.getenv("FLASK_HOST", default_host).strip() or default_host
FLASK_PORT = int(PORT_FROM_PLATFORM or os.getenv("FLASK_PORT", "5000"))

# Comma-separated origins, e.g. "http://localhost:5173,https://example.com"
_origins = os.getenv("ALLOWED_ORIGINS", "*").strip()
if _origins == "*":
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = [origin.strip() for origin in _origins.split(",") if origin.strip()]
