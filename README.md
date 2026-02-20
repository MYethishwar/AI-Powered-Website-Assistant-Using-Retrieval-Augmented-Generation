First: docker run -p 6333:6333 qdrant/qdrant
check : http://localhost:6333


Second: uvicorn app.main:app --reload
Check : http://127.0.0.1:8000/docs


Third: python ui.py
check: http://127.0.0.1:7860