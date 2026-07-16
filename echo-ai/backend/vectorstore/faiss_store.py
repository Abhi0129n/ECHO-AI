import os
import shutil
import logging
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

logger = logging.getLogger("echo_ai.faiss_store")

class FAISSStoreManager:
    def __init__(self, index_path: str, embeddings: Embeddings):
        self.index_path = os.path.abspath(index_path)
        self.embeddings = embeddings
        self.vectorstore: Optional[FAISS] = None
        self.load_index()

    def load_index(self) -> None:
        """Loads FAISS index from the local disk if it exists."""
        if os.path.exists(self.index_path) and os.path.exists(os.path.join(self.index_path, "index.faiss")):
            try:
                self.vectorstore = FAISS.load_local(
                    self.index_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Loaded existing FAISS index from {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to load FAISS index from {self.index_path}: {str(e)}. Starting fresh.")
                self.vectorstore = None
        else:
            logger.info("No existing FAISS index found. Deferring creation until indexing.")
            self.vectorstore = None

    def save_index(self) -> None:
        """Saves current FAISS index state to disk."""
        if self.vectorstore is not None:
            os.makedirs(self.index_path, exist_ok=True)
            self.vectorstore.save_local(self.index_path)
            logger.info(f"Saved FAISS index to {self.index_path}")

    def add_documents(self, docs: List[Document], ids: Optional[List[str]] = None) -> List[str]:
        """
        Adds documents with optional custom IDs to the FAISS store.
        Returns the generated list of chunk IDs.
        """
        if not docs:
            return []
            
        if self.vectorstore is None:
            # Create a fresh FAISS store from the first batch of documents
            self.vectorstore = FAISS.from_documents(docs, self.embeddings, ids=ids)
            # FAISS generates string IDs if ids is not specified
            # Let's extract the IDs:
            doc_ids = list(self.vectorstore.docstore._dict.keys())
        else:
            doc_ids = self.vectorstore.add_documents(docs, ids=ids)
            
        self.save_index()
        return doc_ids

    def delete_documents(self, ids: List[str]) -> bool:
        """Deletes vectors from the index matching the list of chunk IDs."""
        if self.vectorstore is None or not ids:
            return False
            
        try:
            # Filter IDs that actually exist in the docstore to avoid FAISS KeyError
            existing_ids = [idx for idx in ids if idx in self.vectorstore.docstore._dict]
            if existing_ids:
                self.vectorstore.delete(existing_ids)
                self.save_index()
                logger.info(f"Deleted {len(existing_ids)} chunk vectors from FAISS index.")
                return True
        except Exception as e:
            logger.error(f"Error deleting FAISS vectors: {str(e)}")
            
        return False

    def rebuild_index(self, docs: List[Document], ids: Optional[List[str]] = None) -> None:
        """Wipes the existing directory index and initializes a new FAISS database."""
        if os.path.exists(self.index_path):
            try:
                shutil.rmtree(self.index_path)
            except Exception as e:
                logger.warning(f"Could not clean index directory: {str(e)}")
                
        self.vectorstore = None
        self.add_documents(docs, ids=ids)

    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4, 
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search. Returns list of document results
        with scores, filtered by similarity threshold.
        """
        if self.vectorstore is None:
            return []
            
        # FAISS search returns (Document, float_L2_distance)
        # Note: L2 distance in FAISS: lower score means higher similarity.
        # For cosine/normalized embeddings, L2 distance is related to similarity.
        # Let's normalize/format the results
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        filtered_results = []
        for doc, score in results:
            # Convert L2 distance score into a similarity score or keep it.
            # In our case, we can filter by similarity threshold.
            # For BGE embeddings, L2 distance is typically between 0 and 2.
            # Let's check similarity. We can treat similarity_score = max(0, 1.0 - (score / 2.0))
            sim_score = max(0.0, 1.0 - (score / 2.0))
            if sim_score >= threshold:
                filtered_results.append({
                    "document": doc,
                    "score": sim_score,
                    "l2_distance": score
                })
                
        return filtered_results
