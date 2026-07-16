import os
import logging
from typing import Dict, Any, List, Optional
from backend.vectorstore.faiss_store import FAISSStoreManager

logger = logging.getLogger("echo_ai.hybrid_search")

class HybridSearcher:
    def __init__(self, faiss_manager: FAISSStoreManager):
        self.faiss_manager = faiss_manager

    def search(
        self, 
        query: str, 
        k: int = 4, 
        threshold: float = 0.3,
        file_path_filter: Optional[str] = None,
        file_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid search combining lexical (keyword) and semantic similarity searches,
        applies metadata filters, and returns a ranked list of matched document chunks.
        """
        # 1. Semantic Search via FAISS
        semantic_results = self.faiss_manager.similarity_search_with_score(
            query=query, k=k * 2, threshold=threshold
        )

        # 2. Keyword Search across FAISS document store chunks
        keyword_results = []
        if self.faiss_manager.vectorstore is not None:
            doc_dict = self.faiss_manager.vectorstore.docstore._dict
            query_terms = query.lower().split()
            
            for doc_id, doc in doc_dict.items():
                content_lower = doc.page_content.lower()
                matches = 0
                for term in query_terms:
                    if term in content_lower:
                        matches += 1
                
                if matches > 0 and query_terms:
                    keyword_score = matches / len(query_terms)
                    keyword_results.append({
                        "document": doc,
                        "score": keyword_score
                    })

        # 3. Combine results using a weighted score: 0.6 * semantic + 0.4 * keyword
        combined: Dict[str, Dict[str, Any]] = {}

        def get_chunk_key(doc) -> str:
            meta = doc.metadata
            return f"{meta.get('file_path')}_chunk_{meta.get('chunk_number', 1)}"

        # Populate semantic results
        for res in semantic_results:
            doc = res["document"]
            key = get_chunk_key(doc)
            combined[key] = {
                "document": doc,
                "semantic_score": res["score"],
                "keyword_score": 0.0,
                "score": res["score"] * 0.6
            }

        # Merge keyword results
        for res in keyword_results:
            doc = res["document"]
            key = get_chunk_key(doc)
            if key in combined:
                combined[key]["keyword_score"] = res["score"]
                combined[key]["score"] = (combined[key]["semantic_score"] * 0.6) + (res["score"] * 0.4)
            else:
                combined[key] = {
                    "document": doc,
                    "semantic_score": 0.0,
                    "keyword_score": res["score"],
                    "score": res["score"] * 0.4
                }

        # 4. Filter and Sort
        final_list = list(combined.values())
        filtered_list = []

        for item in final_list:
            doc = item["document"]
            meta = doc.metadata

            # Apply exact file path filter
            if file_path_filter:
                filter_abs = os.path.abspath(file_path_filter)
                doc_path_abs = os.path.abspath(meta.get("file_path", ""))
                if filter_abs != doc_path_abs:
                    continue

            # Apply file type filter
            if file_type_filter:
                if meta.get("file_type", "").lower() != file_type_filter.lower():
                    continue

            filtered_list.append(item)

        # Sort descending by final combined score
        filtered_list.sort(key=lambda x: x["score"], reverse=True)
        return filtered_list[:k]
