import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")

# This reads your API from .env and creates openAI client
client = OpenAI(api_key = OPENAI_KEY)


qdrant = QdrantClient(
    url = "http://localhost:6333"
)

COLLECTION = "intellentx_docs"  # Here documents embedding are stored

def create_collection():
    qdrant.recreate_collection(
        collection_name=COLLECTION,
        vectors_config = VectorParams(size = 3072, distance=Distance.COSINE)
    )

def embed_and_store(chunks: list[str]):
    vectors  = client.embeddings.create(
        model = "text-embedding-3-large",
        input = chunks
    ).data

    points = [
        {
            "id": i,
            "vector": vectors[i].embedding,
            "payload":{"text": chunks[i]}
        }
        for i in range(len(chunks))
    ]

    qdrant.upsert(
        collection_name = COLLECTION,
        points = points
    )