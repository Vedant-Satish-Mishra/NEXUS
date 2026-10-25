"""
NEXUS Embedder Interface & FastEmbed Implementation (Step 1.C.1)
Uses BAAI/bge-small-en-v1.5 (384 dimensions) via ONNX runtime.
All calls wrapped in asyncio.to_thread to keep the event loop non-blocking.
"""

import asyncio
from typing import List, Protocol
from fastembed import TextEmbedding

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MODEL_NAME = "BAAI/bge-small-en-v1.5"


class Embedder(Protocol):
    dim: int

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    async def embed_query(self, text: str) -> List[float]:
        ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str = MODEL_NAME, batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size
        self.dim = 384
        self._model: TextEmbedding | None = None

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def _embed_docs_sync(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        generator = model.embed(texts, batch_size=self.batch_size)
        return [embedding.tolist() for embedding in generator]

    def _embed_query_sync(self, text: str) -> List[float]:
        model = self._get_model()
        generator = model.embed([text], batch_size=1)
        return next(generator).tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_docs_sync, texts)

    async def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dim
        prefixed = f"{BGE_QUERY_PREFIX}{text}"
        return await asyncio.to_thread(self._embed_query_sync, prefixed)


# Singleton embedder instance
default_embedder = FastEmbedEmbedder()


def get_embedder() -> Embedder:
    return default_embedder

