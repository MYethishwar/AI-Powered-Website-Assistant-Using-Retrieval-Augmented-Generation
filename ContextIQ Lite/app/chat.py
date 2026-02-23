from openai import OpenAI
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY not set!")

client = OpenAI(api_key=OPENAI_KEY)

qdrant = QdrantClient(url="http://localhost:6333")

COLLECTION = "intellentx_docs"

def retrieve_context(query: str, k: int = 5) -> str:
    embedding = client.embeddings.create(
        model="text-embedding-3-large",
        input=query
    ).data[0].embedding

    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=embedding,
        limit=k
    )

    return "\n\n".join([point.payload["text"] for point in hits.points])


def answer_query(query: str) -> str:
    context = retrieve_context(query)

    system_prompt = """
    You are the official AI assistant of IntellentX.
    Only answer using the provided context.
    If the answer is not found, say:
    'I'm not sure based on the available information.'
    """

    prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{query}"

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

    )

    return response.choices[0].message.content
