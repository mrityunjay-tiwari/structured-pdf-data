This repo is for getting structured data from pdfs using Docling for LLM context.

We get :
- Markdown of the document
- Chunks of the document
    - They are generated with taking into consideration the token size of embedding model to be used later.
    - They are generated using HybridChunker
    - They have metadata associated with them
- Metadata of the document

What different routes does : 
- / : It is for the health check of the API.
- /get-structured-data : It is for getting only the markdown of the document.
- /get-chunks-all-meta : It is for getting only the chunks of the document with all the metadata.
- /get-chunks : It is for getting only the chunks of the document with only the selected metadata which are generally useful as otherwise the metadata is too heavy and useless for LLM context, also increases the token size and unnecessary to save in your DB.
- /process-document : It is for processing the document and depending on the size of the document, it returns the markdown and chunks of the document with selected metadata.
    - Why is this important and great to have ?
        - Because if the document is small, we can send the entire markdownto the LLM for processing (as it is already in the exact format as LLM expects) and it will not bloat the context window of the LLM. Also it is faster (in this case) to process the entire markdown than to process the chunks.
        - If the document is large, we will generate and send the chunked data so that they can fed in batches as depending upon the context window of the LLM you are using and you can process them in batches and then stich the results as required. 