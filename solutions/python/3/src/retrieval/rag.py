"""Retrieval over the loan policy documents — three ways.

═══════════════════════════════════════════════════════════════════════
SECTION 3 - RAG: `search` (vector) is PROVIDED — it is the retrieval
step behind the loan_docs agent. The GOING DEEPER exercises add
`keyword_search` and `hybrid_search`, then race all three.        SOLVED.
═══════════════════════════════════════════════════════════════════════

The loan policy documents (in production these are PDFs; here they are
markdown copies of the same content) are chunked by section, embedded,
and stored in the Redis index defined in `src/data/loader.py`. The same
index answers three kinds of query:

  * keyword — BM25 full-text over the chunk text: exact terms, stemming,
    ranked by term frequency. Unbeatable on precise jargon ("eNACH").
  * vector  — embed the question, return the chunks closest in meaning.
    Unbeatable on paraphrase ("how much to close my loan early").
  * hybrid  — run both, fuse the ranked lists with Reciprocal Rank
    Fusion (Redis FT.HYBRID). Robust when a query mixes exact anchors
    with broader meaning.
"""

from redisvl.index import SearchIndex
from redisvl.query import HybridQuery, TextQuery, VectorQuery
from redisvl.query.filter import Tag

from src import config
from src.llm.client import get_vectorizer

RETURN_FIELDS = ["doc_title", "section", "content", "product"]


class LoanDocsRetriever:
    def __init__(self, redis_url: str = config.REDIS_URL):
        self.vectorizer = get_vectorizer()
        self.index = SearchIndex.from_dict(
            docs_index_schema(), redis_url=redis_url
        )

    def search(self, query: str, k: int = config.RETRIEVAL_TOP_K,
               product: str | None = None) -> list[dict]:
        """Vector search: the top-k chunks closest in meaning to the query.
        This is the *retrieve* step of RAG (provided)."""
        embedding = self.vectorizer.embed(query)
        vector_query = VectorQuery(
            vector=embedding,
            vector_field_name="embedding",
            return_fields=RETURN_FIELDS,
            num_results=k,
        )
        if product:
            vector_query.set_filter(Tag("product") == product)
        results = self.index.query(vector_query)
        return [self._chunk(r, distance=float(r["vector_distance"]))
                for r in results]

    def keyword_search(self, query: str,
                       k: int = config.RETRIEVAL_TOP_K) -> list[dict] | None:
        """Full-text search: BM25-ranked keyword matching over the chunk
        text — exact terms, stemming, no embeddings involved.

        ═══════════════════════════════════════════════════════════════
        SECTION 3 - GOING DEEPER (keyword): build a TextQuery over the
        `content` field with the BM25STD scorer and return the chunks
        (include the BM25 score). Solved.
        ═══════════════════════════════════════════════════════════════
        """
        text_query = TextQuery(
            text=query,
            text_field_name="content",
            text_scorer="BM25STD",
            return_fields=RETURN_FIELDS,
            num_results=k,
            stopwords=None,
        )
        results = self.index.query(text_query)
        return [self._chunk(r, score=round(float(r["score"]), 2))
                for r in results]

    def hybrid_search(self, query: str,
                      k: int = config.RETRIEVAL_TOP_K) -> list[dict] | None:
        """Hybrid search: run the keyword and vector paths together and
        fuse the two ranked lists with Reciprocal Rank Fusion (RRF),
        via Redis's FT.HYBRID.

        ═══════════════════════════════════════════════════════════════
        SECTION 3 - GOING DEEPER (hybrid): embed the query, then build a
        HybridQuery over the text field and the vector field with
        combination_method="RRF". Solved.
        ═══════════════════════════════════════════════════════════════
        """
        embedding = self.vectorizer.embed(query)
        hybrid_query = HybridQuery(
            text=query,
            text_field_name="content",
            vector=embedding,
            vector_field_name="embedding",
            vector_search_method="KNN",
            combination_method="RRF",
            return_fields=RETURN_FIELDS,
            num_results=k,
            stopwords=None,
        )
        results = self.index.query(hybrid_query)
        return [self._chunk(r) for r in results]

    @staticmethod
    def _chunk(record: dict, **extra) -> dict:
        return {
            "doc_title": record["doc_title"],
            "section": record["section"],
            "content": record["content"],
            "product": record["product"],
            **extra,
        }

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
