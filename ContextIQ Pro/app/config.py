import os
from dotenv import load_dotenv

load_dotenv()

def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value

# OpenAI
OPENAI_API_KEY = _require("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")   # cheaper by default

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "intellentx_docs")

# SerpAPI
SERP_API_KEY = os.getenv("SERP_API_KEY", "")

# Crawling
MAX_CRAWL_PAGES = int(os.getenv("MAX_CRAWL_PAGES", "20"))
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Retrieval
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
SCORE_THRESHOLD = float(os.getenv("SCORE_THRESHOLD", "0.4"))

# Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")