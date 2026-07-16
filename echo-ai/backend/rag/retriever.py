import os
import logging
from typing import Dict, Any, List, Optional
from backend.knowledge.search import HybridSearcher
from backend.vectorstore.faiss_store import FAISSStoreManager
from backend.embeddings.embedder import LocalEmbedder

logger = logging.getLogger("echo_ai.retriever")

class RAGRetriever:
    # Class-level state tracker to persist context across stateless requests
    last_retrieved_file_path: Optional[str] = None

    def __init__(self, faiss_manager: FAISSStoreManager):
        self.faiss_manager = faiss_manager
        self.searcher = HybridSearcher(faiss_manager)
        
        # Load environment properties
        self.top_k = int(os.getenv("TOP_K", "4"))
        self.threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

    def retrieve(
        self, 
        query: str, 
        file_path_filter: Optional[str] = None, 
        file_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching chunks using Hybrid Search.
        Applies context-aware follow-up bias for relative queries.
        """
        # Determine if query is a relative follow-up question
        is_followup = self._is_followup_query(query)
        active_path = file_path_filter or (RAGRetriever.last_retrieved_file_path if is_followup else None)

        if is_followup and RAGRetriever.last_retrieved_file_path:
            logger.info(f"Context-aware follow-up query detected. Restricting bias search to: {active_path}")

        # Execute search
        results = self.searcher.search(
            query=query,
            k=self.top_k,
            threshold=self.threshold,
            file_path_filter=active_path,
            file_type_filter=file_type_filter
        )

        # Fallback to general search if follow-up restriction returned 0 matches
        if not results and active_path and not file_path_filter:
            logger.info("Follow-up search returned no results. Performing general search...")
            results = self.searcher.search(
                query=query,
                k=self.top_k,
                threshold=self.threshold,
                file_type_filter=file_type_filter
            )

        # Update last retrieved document context based on top result
        if results:
            top_meta = results[0]["document"].metadata
            RAGRetriever.last_retrieved_file_path = top_meta.get("file_path")
            logger.info(f"Updated context-aware active document path to: {RAGRetriever.last_retrieved_file_path}")

        return results

    def _is_followup_query(self, query: str) -> bool:
        """Determines if the query refers to previous context using heuristics."""
        q_lower = query.lower().strip()
        
        # Check relative pronouns and instructions
        relative_keywords = [
            "that", "it", "again", "explain more", "give me an example", 
            "elaborate", "tell me more", "the file", "the document", "this note"
        ]
        
        # Check if query is short or contains relative keywords
        if len(q_lower.split()) <= 4:
            # Short queries like "give examples" or "explain"
            return True
            
        for kw in relative_keywords:
            if kw in q_lower:
                return True
                
        return False
