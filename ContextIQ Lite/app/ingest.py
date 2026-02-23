from app.scraping import fetch_page_text
from langchain_text_splitters import RecursiveCharacterTextSplitter


def ingest_pages(urls: list[str]) -> list[str]:
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 800,
        chunk_overlap = 100
    )

    for url in urls:
        text =  fetch_page_text(url)
        chunks.extend(splitter.split_text(text))

    return  chunks