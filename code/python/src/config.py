"""Central configuration for the WhatsApp banking bot workshop."""

import os
from pathlib import Path

from dotenv import dotenv_values, find_dotenv

# In the containers, DOTENV_PATH points at the repo's .env through a
# directory mount. A freshly saved .env wins over the values compose
# injected at container creation — so editing .env in the Code panel and
# saving reconfigures the api (uvicorn watches the file). Empty lines in
# .env (the template ships every key blank) must NOT override, or a blank
# REDIS_URL= would clobber the compose default.
for _key, _value in dotenv_values(
        os.getenv("DOTENV_PATH") or find_dotenv()).items():
    if _value:
        os.environ[_key] = _value

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

# Redis Context Retriever (managed, Redis Cloud — Section 4). The admin
# key comes from the service you create in the console; the client's
# CTX_API_URL / CTX_MCP_URL env vars override the managed endpoints.
CTX_ADMIN_KEY = os.getenv("CTX_ADMIN_KEY", "")
# Where the deployed surface id + agent key are stored (local Redis)
CTX_DEPLOYMENT_KEY = "ctx:deployment"

# Redis LangCache (managed semantic caching on Redis Cloud — Section 6).
# Created in the Redis Cloud console; the section's steps walk through it.
LANGCACHE_URL = os.getenv("LANGCACHE_URL", "")
LANGCACHE_CACHE_ID = os.getenv("LANGCACHE_CACHE_ID", "")
LANGCACHE_API_KEY = os.getenv("LANGCACHE_API_KEY", "")

# Redis key / index names
DOCS_INDEX_NAME = "idx:faqs"
DOCS_KEY_PREFIX = "faq:"
CUSTOMER_KEY_PREFIX = "customer:"
LOAN_KEY_PREFIX = "loan:"
OFFERS_KEY_PREFIX = "offers:"
NOC_KEY_PREFIX = "noc:"
LAN_COUNTER_KEY = "counter:lan"
ROUTER_NAME = "wa-journey-router"

# Tuning knobs surfaced in the workshop sections
ROUTER_DISTANCE_THRESHOLD = float(os.getenv("ROUTER_DISTANCE_THRESHOLD", "0.7"))
CACHE_SIMILARITY_THRESHOLD = float(os.getenv("CACHE_SIMILARITY_THRESHOLD",
                                             "0.85"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
