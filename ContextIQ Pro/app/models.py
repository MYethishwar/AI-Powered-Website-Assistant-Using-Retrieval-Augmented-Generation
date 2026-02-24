from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class InitRequest(BaseModel):
    urls: List[str] = Field(..., min_length=1, description="Seed URLs to crawl")
    max_pages: Optional[int] = Field(None, ge=1, le=100, description="Max pages to crawl (overrides default)")
    recreate_collection: bool = Field(False, description="Drop and recreate the Qdrant collection before ingesting")


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    context_found: bool


class SearchRequest(BaseModel):
    company_name: str = Field(..., min_length=2, description="Company name to search for")
    max_results: Optional[int] = Field(None, ge=1, le=10)


class StatusResponse(BaseModel):
    status: str
    detail: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    chunks_ingested: int
    pages_or_files: int


