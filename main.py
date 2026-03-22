from fastapi import FastAPI, Request
from docling.document_converter import DocumentConverter

app = FastAPI()

@app.get('/hello')
def say_hello():
    return "Hello World"

@app.get('/get-structured-data')
def get_structured_data(source: str):
    converter = DocumentConverter()
    result = converter.convert(source)

    return result.document.export_to_markdown()