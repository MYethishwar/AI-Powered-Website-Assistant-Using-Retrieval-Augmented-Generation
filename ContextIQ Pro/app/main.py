
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware

from app.vectorstore import create_collection, embed_and_store, collection_exists
from app.ingest import ingest_pages
from app.chat import answer_query
from app.file_ingest import ingest_file
from app.search_engine import search_google
from app.models import (
    InitRequest,
    AskResponse,
    SearchRequest,
    IngestResponse,
    StatusResponse,
)
from app.config import MAX_CRAWL_PAGES, MAX_SEARCH_RESULTS

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure the Qdrant collection exists when the server starts."""
    logger.info("Server starting — ensuring Qdrant collection exists...")
    create_collection(recreate=False)
    yield
    logger.info("Server shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="IntellentX AI Assistant API",
    description="RAG-powered assistant with web crawling, document upload, and web search.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"message": "IntellentX AI Assistant API is running", "version": "2.0.0"}


@app.get("/health", response_model=StatusResponse, tags=["Health"])
def health():
    ready = collection_exists()
    return StatusResponse(
        status="ready" if ready else "not_initialized",
        detail="Qdrant collection exists." if ready else "Run /init or /upload first.",
    )


# ── Ingestion ──────────────────────────────────────────────────────────────────
@app.post("/init", response_model=IngestResponse, tags=["Ingestion"])
def init_store(request: InitRequest):
    """
    Crawl one or more URLs (and their internal pages) and store embeddings.
    Use recreate_collection=true to wipe and rebuild from scratch.
    """
    try:
        create_collection(recreate=request.recreate_collection)

        max_pages = request.max_pages or MAX_CRAWL_PAGES
        chunks = ingest_pages(request.urls, max_pages=max_pages)

        if not chunks:
            raise HTTPException(status_code=422, detail="No content could be extracted from the provided URLs.")

        stored = embed_and_store(chunks)
        return IngestResponse(status="ok", chunks_ingested=stored, pages_or_files=len(request.urls))

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[/init] Unexpected error")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/upload", response_model=IngestResponse, tags=["Ingestion"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a PDF, TXT, or DOCX file and ingest its contents into the knowledge base.
    """
    try:
        chunks = await ingest_file(file)
        stored = embed_and_store(chunks)
        return IngestResponse(status="uploaded", chunks_ingested=stored, pages_or_files=1)

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("[/upload] Unexpected error")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search", response_model=IngestResponse, tags=["Ingestion"])
def search_and_ingest(request: SearchRequest):
    """
    Search Google for a company, scrape the top results, and add them to the knowledge base.
    """
    try:
        num = request.max_results or MAX_SEARCH_RESULTS
        urls = search_google(request.company_name, num_results=num)

        if not urls:
            raise HTTPException(
                status_code=404,
                detail="No search results found. Check your SERP_API_KEY or try a different query.",
            )

        chunks = ingest_pages(urls)
        stored = embed_and_store(chunks)

        return IngestResponse(status="searched", chunks_ingested=stored, pages_or_files=len(urls))

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[/search] Unexpected error")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Query ──────────────────────────────────────────────────────────────────────
@app.get("/ask", response_model=AskResponse, tags=["Query"])
def ask(q: str = Query(..., min_length=2, description="Your question")):
    """
    Ask a question. Returns an answer grounded in the ingested knowledge base.
    """
    try:
        result = answer_query(q)
        return AskResponse(query=q, **result)
    except Exception as exc:
        logger.exception("[/ask] Unexpected error")
        raise HTTPException(status_code=500, detail=str(exc))