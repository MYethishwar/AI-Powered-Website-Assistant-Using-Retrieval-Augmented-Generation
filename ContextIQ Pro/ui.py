import requests
import gradio as gr

from app.config import BACKEND_URL

# ── Backend helpers ────────────────────────────────────────────────────────────

def _post(endpoint: str, **kwargs) -> dict:
    try:
        resp = requests.post(f"{BACKEND_URL}{endpoint}", timeout=120, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to the backend. Is it running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The operation may still be running in the background."}
    except Exception as exc:
        return {"error": str(exc)}


def _get(endpoint: str, **kwargs) -> dict:
    try:
        resp = requests.get(f"{BACKEND_URL}{endpoint}", timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to the backend. Is it running?"}
    except Exception as exc:
        return {"error": str(exc)}


# ── Action functions ───────────────────────────────────────────────────────────

def init_from_urls(url_text: str, max_pages: int, recreate: bool) -> str:
    urls = [u.strip() for u in url_text.strip().splitlines() if u.strip()]
    if not urls:
        return "❌ Please enter at least one URL."

    data = _post(
        "/init",
        json={"urls": urls, "max_pages": max_pages, "recreate_collection": recreate},
    )

    if "error" in data:
        return f"❌ Error: {data['error']}"
    return (
        f"✅ Done! Crawled {data.get('pages_or_files', '?')} seed URL(s), "
        f"stored {data.get('chunks_ingested', '?')} chunks."
    )


def upload_document(file) -> str:
    if file is None:
        return "❌ No file selected."

    with open(file.name, "rb") as f:
        data = _post("/upload", files={"file": (file.name.split("/")[-1], f)})

    if "error" in data:
        return f"❌ Error: {data['error']}"
    return f"✅ Uploaded! Stored {data.get('chunks_ingested', '?')} chunks."


def search_company(company_name: str, max_results: int) -> str:
    if not company_name.strip():
        return "❌ Please enter a company name."

    data = _post("/search", json={"company_name": company_name.strip(), "max_results": max_results})

    if "error" in data:
        return f"❌ Error: {data['error']}"
    return (
        f"✅ Searched & ingested! Found {data.get('pages_or_files', '?')} pages, "
        f"stored {data.get('chunks_ingested', '?')} chunks."
    )


def chat_fn(message: str, history: list) -> str:
    if not message.strip():
        return "Please enter a question."

    data = _get("/ask", params={"q": message})

    if "error" in data:
        return f"❌ Error: {data['error']}"

    answer = data.get("answer", "No answer returned.")
    sources = data.get("sources", [])
    context_found = data.get("context_found", False)

    if not context_found:
        return answer

    if sources:
        source_list = "\n".join(f"• {s}" for s in sources[:5])
        return f"{answer}\n\n---\n**Sources:**\n{source_list}"

    return answer


# ── UI Layout ──────────────────────────────────────────────────────────────────

with gr.Blocks(title="AI Website Assistant") as demo:
    gr.Markdown("# 🤖 AI Website Assistant Assistant")
    gr.Markdown("Ask anything about IntellentX — powered by RAG.")

    with gr.Tabs():

        # ── Tab 1: Chat ──────────────────────────────────────────────────────
        with gr.Tab("💬 Chat"):
            gr.ChatInterface(
                fn=chat_fn,
                chatbot=gr.Chatbot(height=500),
                textbox=gr.Textbox(placeholder="Ask a question about IntellentX...", scale=7),
            )

        # ── Tab 2: URL Crawl ─────────────────────────────────────────────────
        with gr.Tab("🌐 Crawl Website"):
            gr.Markdown("### Crawl a website to build the knowledge base")
            url_input = gr.Textbox(
                label="Website URLs (one per line)",
                placeholder="https://intellentx.com\nhttps://intellentx.com/about",
                lines=4,
            )
            with gr.Row():
                max_pages_slider = gr.Slider(1, 50, value=20, step=1, label="Max pages to crawl")
                recreate_checkbox = gr.Checkbox(label="🔄 Recreate collection (wipes existing data)", value=False)

            crawl_btn = gr.Button("🚀 Start Crawling", variant="primary")
            crawl_status = gr.Textbox(label="Status", interactive=False)

            crawl_btn.click(
                fn=init_from_urls,
                inputs=[url_input, max_pages_slider, recreate_checkbox],
                outputs=crawl_status,
            )

        # ── Tab 3: Document Upload ───────────────────────────────────────────
        with gr.Tab("📄 Upload Document"):
            gr.Markdown("### Upload a PDF, TXT, or DOCX file")
            file_input = gr.File(
                label="Choose file",
                file_types=[".pdf", ".txt", ".docx"],
            )
            upload_btn = gr.Button("⬆️ Upload & Ingest", variant="primary")
            upload_status = gr.Textbox(label="Status", interactive=False)

            upload_btn.click(
                fn=upload_document,
                inputs=file_input,
                outputs=upload_status,
            )

        # ── Tab 4: Web Search ────────────────────────────────────────────────
        with gr.Tab("🔍 Search & Ingest"):
            gr.Markdown("### Search the web for company info and ingest it")
            company_input = gr.Textbox(
                label="Company name",
                placeholder="e.g. IntellentX AI",
            )
            max_results_slider = gr.Slider(1, 10, value=5, step=1, label="Max search results to ingest")
            search_btn = gr.Button("🔍 Search & Ingest", variant="primary")
            search_status = gr.Textbox(label="Status", interactive=False)

            search_btn.click(
                fn=search_company,
                inputs=[company_input, max_results_slider],
                outputs=search_status,
            )

if __name__ == "__main__":
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Soft(primary_hue="blue"),
    )


