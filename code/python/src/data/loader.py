"""Seed Redis with the workshop dataset.

Runs once on API startup (idempotent):
  * customers  -> HASH  customer:<id>
  * loans      -> JSON  loan:<lan>          (+ set customer:<id>:loans)
  * offers     -> JSON  offers:<customer_id>
  * loan docs  -> chunked by `## ` heading, embedded, loaded into idx:loan_docs
"""

import json
import re

import redis

from src import config
from src.llm.client import get_vectorizer
from src.retrieval.rag import docs_index_schema

from redisvl.index import SearchIndex


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def ensure_loaded() -> dict:
    """Load customers, loans, offers, and the loan-docs vector index."""
    r = get_redis()
    summary = {"customers": 0, "loans": 0, "offers": 0, "doc_chunks": 0,
               "skipped": False}

    if r.exists("workshop:loaded"):
        summary["skipped"] = True
        return summary

    dataset = json.loads((config.DATA_DIR / "customers.json").read_text())

    for customer in dataset["customers"]:
        r.hset(f"{config.CUSTOMER_KEY_PREFIX}{customer['customer_id']}",
               mapping={k: str(v) for k, v in customer.items()})
        summary["customers"] += 1

    for loan in dataset["loans"]:
        r.json().set(f"{config.LOAN_KEY_PREFIX}{loan['lan']}", "$", loan)
        r.sadd(f"{config.CUSTOMER_KEY_PREFIX}{loan['customer_id']}:loans",
               loan["lan"])
        summary["loans"] += 1

    for entry in dataset["offers"]:
        r.json().set(f"{config.OFFERS_KEY_PREFIX}{entry['customer_id']}", "$",
                     entry["offers"])
        summary["offers"] += 1

    summary["doc_chunks"] = load_loan_docs()

    r.set("workshop:loaded", "1")
    return summary


def load_loan_docs() -> int:
    """Chunk each loan document on its `## ` section headings and embed."""
    chunks = []
    for path in sorted((config.DATA_DIR / "loan_docs").glob("*.md")):
        text = path.read_text()
        title = _first_match(r"^# (.+)$", text) or path.stem
        product = _first_match(r"^product: (.+)$", text) or "general"
        for section, body in _split_sections(text):
            chunks.append({
                "chunk_id": f"{path.stem}:{_slug(section)}",
                "doc_title": title,
                "section": section,
                "content": body,
                "product": product,
            })

    vectorizer = get_vectorizer()
    embeddings = vectorizer.embed_many(
        [f"{c['doc_title']} — {c['section']}\n{c['content']}" for c in chunks],
        as_buffer=True,
    )
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    index = SearchIndex.from_dict(docs_index_schema(),
                                  redis_url=config.REDIS_URL)
    index.create(overwrite=True, drop=True)
    index.load(chunks, id_field="chunk_id")
    return len(chunks)


def _split_sections(text: str) -> list[tuple[str, str]]:
    sections = []
    parts = re.split(r"^## ", text, flags=re.MULTILINE)[1:]
    for part in parts:
        heading, _, body = part.partition("\n")
        sections.append((heading.strip(), body.strip()))
    return sections


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
