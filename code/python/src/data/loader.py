"""Seed the workshop's Redis Cloud database with the FAQ knowledge base.

Runs once on API startup (idempotent). It loads ONE thing: the bank's
FAQs (data/faqs.json), embedded into the vector index that powers the
RAG section.

Deliberately absent: customers, loans, and offers. The bank's structured
records enter the database in Section 4 — imported through the Redis
Context Retriever, the way RDI would feed it from core banking in
production. Until then, the servicing agents have nothing to read, and
that's the point.
"""

import json

import redis

from src import config
from src.llm.client import get_vectorizer

from redisvl.index import SearchIndex

PRODUCT_LABELS = {
    "personal_loan": "Personal loans",
    "topup_loan": "Top-up loans",
    "balance_transfer": "Balance transfer",
    "home_decor_loan": "Home decor loans",
    "noc": "NOC",
    "preapproval": "Pre-approved offers",
    "general": "Loans in general",
}


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def ensure_loaded() -> dict:
    """Embed and index the FAQ knowledge base (skips if already loaded)."""
    r = get_redis()
    if r.exists("workshop:loaded"):
        return {"faqs": 0, "skipped": True}

    count = load_faqs()
    r.set("workshop:loaded", "1")
    return {"faqs": count, "skipped": False}


def load_faqs() -> int:
    """One index record per FAQ: the question is the retrievable unit."""
    faqs = json.loads((config.DATA_DIR / "faqs.json").read_text())["faqs"]

    records = []
    for faq in faqs:
        label = PRODUCT_LABELS.get(faq["product"], faq["product"])
        records.append({
            "chunk_id": faq["id"],
            "doc_title": f"FAQ — {label}",
            "section": faq["question"],
            "content": f"Q: {faq['question']}\nA: {faq['answer']}",
            "product": faq["product"],
        })

    vectorizer = get_vectorizer()
    embeddings = vectorizer.embed_many(
        [record["content"] for record in records], as_buffer=True)
    for record, embedding in zip(records, embeddings):
        record["embedding"] = embedding

    from src.retrieval.rag import docs_index_schema
    index = SearchIndex.from_dict(docs_index_schema(),
                                  redis_url=config.REDIS_URL)
    index.create(overwrite=True, drop=True)
    index.load(records, id_field="chunk_id")
    return len(records)
