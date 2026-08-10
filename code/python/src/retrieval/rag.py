"""Vector retrieval over the loan policy documents (used from Section 3 on).

The loan policy documents (in production these are PDFs; here they are
markdown copies of the same content) are chunked by section, embedded, and
stored in the Redis index defined in `src/data/loader.py`. This module is the
*retrieve* step of RAG: embed the question, find the closest chunks.
"""

from redisvl.index import SearchIndex
from redisvl.query import VectorQuery
from redisvl.query.filter import Tag

from src import config
from src.llm.client import get_vectorizer


class LoanDocsRetriever:
    def __init__(self, redis_url: str = config.REDIS_URL):
        self.vectorizer = get_vectorizer()
        self.index = SearchIndex.from_dict(
            docs_index_schema(), redis_url=redis_url
        )

    def search(self, query: str, k: int = config.RETRIEVAL_TOP_K,
               product: str | None = None) -> list[dict]:
        """Return the top-k chunks closest in meaning to the query."""
        embedding = self.vectorizer.embed(query)
        vector_query = VectorQuery(
            vector=embedding,
            vector_field_name="embedding",
            return_fields=["doc_title", "section", "content", "product"],
            num_results=k,
        )
        if product:
            vector_query.set_filter(Tag("product") == product)
        results = self.index.query(vector_query)
        return [
            {
                "doc_title": r["doc_title"],
                "section": r["section"],
                "content": r["content"],
                "product": r["product"],
                "distance": float(r["vector_distance"]),
            }
            for r in results
        ]

    @staticmethod
    def format_context(chunks: list[dict]) -> str:
        """Lay retrieved chunks out as numbered context entries for the prompt."""
        lines = []
        for i, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{i}] {chunk['doc_title']} — {chunk['section']}\n{chunk['content']}"
            )
        return "\n\n".join(lines)


def docs_index_schema() -> dict:
    """RedisVL schema for the loan document chunks."""
    return {
        "index": {
            "name": config.DOCS_INDEX_NAME,
            "prefix": config.DOCS_KEY_PREFIX,
            "storage_type": "hash",
        },
        "fields": [
            {"name": "doc_title", "type": "text"},
            {"name": "section", "type": "text"},
            {"name": "content", "type": "text"},
            {"name": "product", "type": "tag"},
            {
                "name": "embedding",
                "type": "vector",
                "attrs": {
                    "dims": config.EMBEDDING_DIMS,
                    "distance_metric": "cosine",
                    "algorithm": "hnsw",
                    "datatype": "float32",
                },
            },
        ],
    }
