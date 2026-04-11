from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

converter = None
chunker = None

@app.get('/')
def health_check():
    return {"status": "healthy", "message": "API is running!"}

@app.get('/hello')
def say_hello():
    return "Hello World"

@app.get('/get-structured-data')
def get_structured_data(source: str):
    global converter
    if converter is None:
        print("Initializing DocumentConverter with restricted threads & PyPdfium (OOM Fix)")
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device="cpu")
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        
    result = converter.convert(source)

    return result.document.export_to_markdown()

@app.get('/get-chunks-all-meta')
def get_chunks_all_meta(source: str):
    global converter
    global chunker
    
    if converter is None:
        print("Initializing DocumentConverter with restricted threads & PyPdfium (OOM Fix)")
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device="cpu")
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    if chunker is None:
        print("Initializing HybridChunker and downloading Tokenizer (happens only once)")
        import warnings

        warnings.filterwarnings("ignore", category=FutureWarning)
        
        from transformers import AutoTokenizer
        from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
        from docling.chunking import HybridChunker
        
        print("Downloading nvidia/llama-nemotron tokenizer...")
        hf_tokenizer = AutoTokenizer.from_pretrained("nvidia/llama-nemotron-embed-vl-1b-v2")
        
        tokenizer = HuggingFaceTokenizer(tokenizer=hf_tokenizer, max_tokens=2048)
        
        chunker = HybridChunker(tokenizer=tokenizer, merge_peers=True)

    print(f"Parsing document: {source}")
    result = converter.convert(source)

    print("Generating chunks...")
    chunk_iter = chunker.chunk(dl_doc=result.document)
    
    import json
    chunks_list = []
    for chunk in chunk_iter:
        chunk_dict = json.loads(chunk.model_dump_json())
        chunks_list.append(chunk_dict)

    return {"chunks": chunks_list, "total_chunks": len(chunks_list)}

@app.get('/get-chunks')
def get_chunks(source: str):
    global converter
    global chunker
    
    if converter is None:
        print("Initializing DocumentConverter with restricted threads & PyPdfium (OOM Fix)")
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device="cpu")
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    if chunker is None:
        print("Initializing HybridChunker")
        import warnings
        warnings.filterwarnings("ignore", category=FutureWarning)
        
        from transformers import AutoTokenizer
        from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
        from docling.chunking import HybridChunker
        
        print("Downloading nvidia/llama-nemotron tokenizer...")
        hf_tokenizer = AutoTokenizer.from_pretrained("nvidia/llama-nemotron-embed-vl-1b-v2")
        tokenizer = HuggingFaceTokenizer(tokenizer=hf_tokenizer, max_tokens=2048)
        chunker = HybridChunker(tokenizer=tokenizer, merge_peers=True)

    print(f"Parsing document: {source}")
    result = converter.convert(source)

    print("Generating chunks...")
    chunk_iter = chunker.chunk(dl_doc=result.document)
    
    import json
    chunks_list = []
    for chunk in chunk_iter:
        chunk_dict = json.loads(chunk.model_dump_json())
        meta = chunk_dict.get("meta", {})
        doc_items = meta.get("doc_items", [])
        
        headings = meta.get("headings") or []
        
        labels = list(set([item.get("label") for item in doc_items if item.get("label")]))
        
        page_numbers = set()
        for item in doc_items:
            for prov in item.get("prov", []):
                if "page_no" in prov:
                    page_numbers.add(prov["page_no"])
                    
        origin = meta.get("origin", {})
        filename = origin.get("filename", "") if origin else ""

        chunks_list.append({
            "text": chunk.text,
            "meta": {
                "headings": headings,
                "page_numbers": list(page_numbers),
                "types": labels,
                "filename": filename
            }
        })

    return {"chunks": chunks_list, "total_chunks": len(chunks_list), "markdown": result.document.export_to_markdown()}

@app.get('/process-document')
def process_document(source: str):

    global converter
    global chunker
    
    if converter is None:
        print("Initializing DocumentConverter")
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=1, device="cpu")
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )

    print(f"Parsing document: {source}")
    result = converter.convert(source)
    markdown_text = result.document.export_to_markdown()

    if len(markdown_text) < 30000:
        print(f"Document is small ({len(markdown_text)} chars). Returning the markdown.")
        return {
            "status": "success",
            "doc_type": "markdown",
            "data": markdown_text
        }
    else:
        print(f"Document is large ({len(markdown_text)} chars). Generating chunks...")

        if chunker is None:
            print("Initializing HybridChunker")
            import warnings
            warnings.filterwarnings("ignore", category=FutureWarning)
            
            from transformers import AutoTokenizer
            from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
            from docling.chunking import HybridChunker
            
            print("Downloading nvidia/llama-nemotron tokenizer...")
            hf_tokenizer = AutoTokenizer.from_pretrained("nvidia/llama-nemotron-embed-vl-1b-v2")
            tokenizer = HuggingFaceTokenizer(tokenizer=hf_tokenizer, max_tokens=2048)
            chunker = HybridChunker(tokenizer=tokenizer, merge_peers=True)

        chunk_iter = chunker.chunk(dl_doc=result.document)
        import json
        chunks_list = []
        for chunk in chunk_iter:
            chunk_dict = json.loads(chunk.model_dump_json())
            meta = chunk_dict.get("meta", {})
            doc_items = meta.get("doc_items", [])
            
            headings = meta.get("headings") or []
            labels = list(set([item.get("label") for item in doc_items if item.get("label")]))
            
            page_numbers = set()
            for item in doc_items:
                for prov in item.get("prov", []):
                    if "page_no" in prov:
                        page_numbers.add(prov["page_no"])
                        
            origin = meta.get("origin", {})
            filename = origin.get("filename", "") if origin else ""

            chunks_list.append({
                "text": chunk.text,
                "meta": {
                    "headings": headings,
                    "page_numbers": list(page_numbers),
                    "types": labels,
                    "filename": filename
                }
            })

        return {
            "status": "success",
            "doc_type": "chunks",
            "data": chunks_list
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)