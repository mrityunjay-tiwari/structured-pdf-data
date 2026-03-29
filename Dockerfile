FROM python:3.11

RUN useradd -m -u 1000 user

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user ./requirements.txt $HOME/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r $HOME/app/requirements.txt

# Pre-download tokenizers and layout models to bake them into the Docker image
RUN python -c "\
import warnings; warnings.filterwarnings('ignore'); \
from transformers import AutoTokenizer; \
AutoTokenizer.from_pretrained('nvidia/llama-nemotron-embed-vl-1b-v2'); \
from docling.document_converter import DocumentConverter; \
DocumentConverter()"

COPY --chown=user . $HOME/app

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]