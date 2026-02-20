from fastapi import FastAPI, HTTPException
from typing import List
from app.vectorstore import create_collection, embed_and_store
from app.ingest import ingest_pages
from app.chat import answer_query

app = FastAPI()

@app.get("/")
def root():
    return {"message": "server is running"}

@app.post("/init")
def init_store(urls:List[str]):
    create_collection()
    chunks = ingest_pages(urls)
    embed_and_store(chunks)
    return {"status": "ok", "ingested": len(chunks)}


@app.get("/ask")
def ask(q: str):
    try:
        answer = answer_query(q)
        return {"query": q, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))