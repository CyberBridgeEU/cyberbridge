from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

# Load model once at module level
model = SentenceTransformer("all-MiniLM-L6-v2")
MODEL_NAME = "all-MiniLM-L6-v2"
DIMENSIONS = 384

app = FastAPI(title="CyberBridge Embeddings Service")


class EmbedRequest(BaseModel):
    text: Optional[str] = None
    texts: Optional[List[str]] = None


class EmbedResponse(BaseModel):
    embedding: Optional[List[float]] = None
    embeddings: Optional[List[List[float]]] = None


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "dimensions": DIMENSIONS}


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    if request.text is not None:
        vector = model.encode(request.text).tolist()
        return EmbedResponse(embedding=vector)
    elif request.texts is not None:
        vectors = model.encode(request.texts).tolist()
        return EmbedResponse(embeddings=vectors)
    else:
        return EmbedResponse()
