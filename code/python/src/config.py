"""Central configuration for the WhatsApp banking bot workshop."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# LLM / embeddings (OpenAI-compatible)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1536"))

# Data directory (mounted at /workshop/data inside the api container)
try:
    # repo checkout: <root>/code/python/src/config.py -> <root>/data
    _DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
except IndexError:
    # container layout is shallower (/app/src); DATA_DIR env is set there
    _DEFAULT_DATA_DIR = Path("/workshop/data")
DATA_DIR = Path(os.getenv("DATA_DIR", str(_DEFAULT_DATA_DIR)))

# Redis Agent Memory Server (the Agent Memory component of Redis Iris)
AGENT_MEMORY_URL = os.getenv("AGENT_MEMORY_URL", "http://localhost:8088")

# Redis key / index names
DOCS_INDEX_NAME = "idx:loan_docs"
DOCS_KEY_PREFIX = "doc:"
CUSTOMER_KEY_PREFIX = "customer:"
LOAN_KEY_PREFIX = "loan:"
OFFERS_KEY_PREFIX = "offers:"
NOC_KEY_PREFIX = "noc:"
LAN_COUNTER_KEY = "counter:lan"
ROUTER_NAME = "wa-journey-router"
CACHE_NAME = "wa-reply-cache"

# Tuning knobs surfaced in the workshop sections
ROUTER_DISTANCE_THRESHOLD = float(os.getenv("ROUTER_DISTANCE_THRESHOLD", "0.7"))
CACHE_DISTANCE_THRESHOLD = float(os.getenv("CACHE_DISTANCE_THRESHOLD", "0.25"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
