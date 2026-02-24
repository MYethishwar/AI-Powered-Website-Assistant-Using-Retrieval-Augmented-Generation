import logging

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from fastapi import UploadFile

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _extract_pdf(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    pages = [page.get_text() for page in doc]
    return "\n".join(pages)


def _extract_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def _extract_docx(content: bytes) -> str:
    import io
    doc = DocxDocument(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


_EXTRACTORS = {
    ".pdf": _extract_pdf,
    ".txt": _extract_txt,
    ".docx": _extract_docx,
}


async def ingest_file(file: UploadFile) -> list[dict]:
    """
    Read an uploaded file, extract its text, and return chunked dicts
    with source metadata.

    Raises ValueError for unsupported file types.
    """
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    content = await file.read()
    logger.info(f"[file_ingest] Processing '{filename}' ({len(content)} bytes)")

    extractor = _EXTRACTORS[ext]
    text = extractor(content)

    if not text.strip():
        raise ValueError(f"No extractable text found in '{filename}'.")

    raw_chunks = _splitter.split_text(text)
    chunks = [
        {"text": chunk, "source": f"upload:{filename}"}
        for chunk in raw_chunks
        if chunk.strip()
    ]

    logger.info(f"[file_ingest] '{filename}' → {len(chunks)} chunks")
    return chunks


