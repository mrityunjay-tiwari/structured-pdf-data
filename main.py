from fastapi import FastAPI, Request
from docling.document_converter import DocumentConverter
import os
import uvicorn

app = FastAPI()

@app.get('/hello')
def say_hello():
    return "Hello World"

@app.get('/get-structured-data')
def get_structured_data(source: str):
    converter = DocumentConverter()
    result = converter.convert(source)

    return result.document.export_to_markdown()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)