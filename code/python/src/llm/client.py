"""LLM and embedding clients shared by every section of the workshop."""

from langchain_openai import ChatOpenAI
from redisvl.utils.vectorize import OpenAITextVectorizer

from src import config


def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    """The chat model behind every agent in the graph."""
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=temperature,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL,
        timeout=30,
    )


def get_vectorizer() -> OpenAITextVectorizer:
    """The embedding model used by retrieval, routing, memory, and caching."""
    return OpenAITextVectorizer(
        model=config.EMBEDDING_MODEL,
        api_config={
            "api_key": config.OPENAI_API_KEY,
            "base_url": config.OPENAI_BASE_URL,
        },
    )
