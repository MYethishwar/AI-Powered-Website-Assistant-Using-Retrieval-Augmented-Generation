import gradio as gr
import requests

BACKEND_URL = "http://127.0.0.1:8000/ask"

def ask_backend(message, history):
    try:
        response = requests.get(
            BACKEND_URL,
            params = {"q": message},
            timeout = 30
        )
        data = response.json()
        answer  = data.get("answer", "No Response.")
    except Exception as e:
        answer = f"Error : {str(e)}"

    return answer

with gr.Blocks(title="Intellentx AI Assistant") as demo:
    gr.Markdown("# IntellentX AI Assistant")
    gr.Markdown("#Ask Anything about Intellentx")

    gr.ChatInterface(
        fn=ask_backend
    )

demo.launch(share = True)

