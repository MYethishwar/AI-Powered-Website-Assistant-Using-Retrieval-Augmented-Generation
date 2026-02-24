import logging
import uuid

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, ScoredPoint

from app.config import (
    OPENAI_API_KEY,
    QDRANT_URL,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    TOP_K_RESULTS,
    SCORE_THRESHOLD,
)

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY)
qdrant = QdrantClient(url=QDRANT_URL)


# ── Collection Management ──────────────────────────────────────────────────────

def create_collection(recreate: bool = False) -> None:
    """Create the Qdrant collection if it doesn't exist. Optionally recreate."""
    existing = {c.name for c in qdrant.get_collections().collections}

    if COLLECTION_NAME in existing:
        if recreate:
            logger.info(f"[vectorstore] Deleting existing collection '{COLLECTION_NAME}'")
            qdrant.delete_collection(COLLECTION_NAME)
        else:
            logger.info(f"[vectorstore] Collection '{COLLECTION_NAME}' already exists, skipping.")
            return

    logger.info(f"[vectorstore] Creating collection '{COLLECTION_NAME}' (dim={EMBEDDING_DIM})")
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )


# ── Embedding & Storage ────────────────────────────────────────────────────────

def _embed_batch(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_and_store(chunks: list[dict], batch_size: int = 100) -> int:
    """
    Embed and upsert chunks into Qdrant.
    Each chunk must be {"text": str, "source": str}.
    Returns the number of points stored.
    """
    if not chunks:
        logger.warning("[vectorstore] embed_and_store called with empty chunks list.")
        return 0

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]

        try:
            vectors = _embed_batch(texts)
        except Exception as exc:
            logger.error(f"[vectorstore] Embedding batch {i}-{i+len(batch)} failed: {exc}")
            continue

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vectors[j],
                payload={"text": batch[j]["text"], "source": batch[j].get("source", "unknown")},
            )
            for j in range(len(batch))
        ]

        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        total += len(points)
        logger.info(f"[vectorstore] Stored batch {i//batch_size + 1}: {len(points)} points")

    logger.info(f"[vectorstore] Total stored: {total} points")
    return total


# ── Retrieval ──────────────────────────────────────────────────────────────────

def retrieve_chunks(query: str, k: int = TOP_K_RESULTS) -> list[ScoredPoint]:
    """
    Embed query and retrieve top-k similar chunks from Qdrant.
    Filters by SCORE_THRESHOLD so low-confidence chunks are excluded.
    """
    try:
        embedding = openai_client.embeddings.create(
            model=EMBEDDING_MODEL, input=query
        ).data[0].embedding
    except Exception as exc:
        logger.error(f"[vectorstore] Query embedding failed: {exc}")
        return []

    hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=k,
        score_threshold=SCORE_THRESHOLD,
    )

    return hits.points


def collection_exists() -> bool:
    existing = {c.name for c in qdrant.get_collections().collections}
    return COLLECTION_NAME in existing


