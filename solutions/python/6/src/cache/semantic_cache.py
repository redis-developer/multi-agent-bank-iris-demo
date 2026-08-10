"""Semantic caching of bot replies.

═══════════════════════════════════════════════════════════════════════
SECTION 6 - SEMANTIC CACHING: solved.
═══════════════════════════════════════════════════════════════════════

"What is the foreclosure charge?", "foreclosure fees?", and "how much to
close my loan early?" are the same question in different words. A semantic
cache stores each generated answer under the *embedding* of its question,
so any paraphrase within the distance threshold is served straight from
Redis — no retrieval, no LLM call, no token cost. This is the pattern
Redis LangCache productises.

Only impersonal answers belong here: policy questions from the loan docs
are shared across all customers, while "what's MY outstanding balance" is
not. The chat service enforces that rule; this class is just the cache.
"""

from src import config
from src.llm.client import get_vectorizer

try:  # redisvl >= 0.6
    from redisvl.extensions.cache.llm import SemanticCache
except ImportError:  # older redisvl
    from redisvl.extensions.llmcache import SemanticCache


class ReplyCache:
    def __init__(self, redis_url: str = config.REDIS_URL):
        self.cache = SemanticCache(
            name=config.CACHE_NAME,
            redis_url=redis_url,
            vectorizer=get_vectorizer(),
            distance_threshold=config.CACHE_DISTANCE_THRESHOLD,
        )

    def check(self, message: str) -> str | None:
        """Return a cached reply for a semantically equivalent question."""
        hits = self.cache.check(prompt=message, num_results=1)
        if hits:
            return hits[0]["response"]
        return None

    def store(self, message: str, reply: str) -> None:
        """Store a freshly generated reply under this question."""
        self.cache.store(prompt=message, response=reply)
