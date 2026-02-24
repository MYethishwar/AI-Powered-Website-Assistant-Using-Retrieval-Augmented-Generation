import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY, CHAT_MODEL
from app.vectorstore import retrieve_chunks

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def _format_context(hits) -> tuple[str, list[str]]:
    """Return (context_text, list_of_sources) from Qdrant hits."""
    if not hits:
        return "", []

    parts = []
    sources = []
    for hit in hits:
        text = hit.payload.get("text", "")
        # Truncate each chunk to 300 words to save tokens
        words = text.split()
        if len(words) > 300:
            text = " ".join(words[:300]) + "..."
        parts.append(text)
        source = hit.payload.get("source", "unknown")
        if source not in sources:
            sources.append(source)

    return "\n\n---\n\n".join(parts), sources


def answer_query(query: str) -> dict:
    """
    Retrieve relevant context from Qdrant and generate an answer via GPT.

    Returns:
        {
            "answer": str,
            "sources": list[str],
            "context_found": bool,
        }
    """
    hits = retrieve_chunks(query)
    context, sources = _format_context(hits)
    context_found = bool(context)

    if not context_found:
        logger.info(f"[chat] No context found for query: '{query}'")
        return {
            "answer": (
                "I'm sorry, I don't have enough information to answer that. "
                "Please contact IntellentX directly for more details."
            ),
            "sources": [],
            "context_found": False,
        }

    system_prompt = (
        "You are the official AI assistant for IntellentX. "
        "Answer ONLY using the CONTEXT provided. "
        "If the answer is not in the context, say: I'm sorry, I don't have enough information to answer that. "
        "Be concise, professional, and helpful. Never make up facts."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{query}"},
    ]

    try:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content
    except Exception as exc:
        logger.error(f"[chat] OpenAI completion failed: {exc}")
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    return {
        "answer": answer,
        "sources": sources,
        "context_found": True,
    }


