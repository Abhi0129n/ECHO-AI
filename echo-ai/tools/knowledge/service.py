import os
import logging
from typing import List, Dict, Any, Optional
from backend.knowledge.indexer import DocumentIndexer
from backend.rag.retriever import RAGRetriever
from backend.rag.chain import RAGChain
from backend.ai.llm import LLMService

logger = logging.getLogger("echo_ai.knowledge_service")

class KnowledgeService:
    def __init__(self):
        # Setup Knowledge indexer, retriever, and RAG chain
        self.indexer = DocumentIndexer()
        self.retriever = RAGRetriever(faiss_manager=self.indexer.faiss_manager)
        self.rag_chain = RAGChain(llm_service=self.indexer.embedder.model if hasattr(self.indexer.embedder, "model_name") else None)
        # Override to use LLMService properly
        self.rag_chain = RAGChain()

    def index_document(self, file_path: str) -> Dict[str, Any]:
        """Indexes a new document into the knowledge base vector store."""
        return self.indexer.index_document(file_path)

    def delete_document(self, file_path: str) -> bool:
        """Deletes a document from the index registry and vector store."""
        return self.indexer.delete_document(file_path)

    def search(
        self, 
        query: str, 
        file_path_filter: Optional[str] = None, 
        file_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs context-aware RAG search across documents."""
        # 1. Retrieve top chunks
        chunks = self.retriever.retrieve(
            query=query, 
            file_path_filter=file_path_filter, 
            file_type_filter=file_type_filter
        )
        # 2. Run RAG chain to synthesize response
        return self.rag_chain.generate_answer(query, chunks)

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all indexed documents."""
        return self.indexer.registry.list_documents()

    def reindex(self) -> Dict[str, Any]:
        """Wipes and index rebuilds all registered documents."""
        return self.indexer.reindex_all()

    def summarize_document(self, file_path: str) -> str:
        """Generates an executive summary of the document using LLM context segments."""
        file_path = os.path.abspath(file_path)
        record = self.indexer.registry.get_document(file_path)
        if not record:
            raise ValueError(f"Document '{file_path}' is not indexed. Please index it first.")

        chunks = []
        if self.indexer.faiss_manager.vectorstore is not None:
            doc_dict = self.indexer.faiss_manager.vectorstore.docstore._dict
            chunk_ids = record.get("chunk_ids", [])
            for cid in chunk_ids:
                if cid in doc_dict:
                    chunks.append(doc_dict[cid].page_content)

        if not chunks:
            raise ValueError(f"No text content found for document '{file_path}'")

        # Combine text segments safely within token context thresholds
        full_text = "\n".join(chunks)
        truncated_text = full_text[:12000]  # Take first ~2000-3000 tokens

        sys_prompt = (
            "You are a summarizing assistant. Summarize the following document content "
            "into a brief, professional executive summary with bullet points."
        )
        llm = LLMService()
        summary = llm.generate_response(sys_prompt, f"Document Content:\n{truncated_text}")
        return summary.strip()
