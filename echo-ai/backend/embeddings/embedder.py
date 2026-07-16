import os
from typing import List
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

class LocalEmbedder(Embeddings):
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.model_name = model_name
        # Generates local embeddings using SentenceTransformer (CPU execution default)
        self.model = SentenceTransformer(self.model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a list of documents locally using SentenceTransformer."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embeds a single query text locally using SentenceTransformer."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
