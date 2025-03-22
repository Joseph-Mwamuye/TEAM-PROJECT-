import os
from dotenv import load_dotenv

load_dotenv()

API_PREFIX = "/api/v1"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

CURRENCY_API_URL = "https://open.er-api.com/v6/latest/USD"

RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")

CACHE_RESULTS = True
CACHE_TTL = 3600