import logging
import time
from typing import Dict, Any, List, Optional
from backend.ai.llm import LLMService
from backend.rag.prompts import RAG_SYSTEM_PROMPT

logger = logging.getLogger("echo_ai.rag_chain")

class RAGChain:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()

    def generate_answer(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats retrieved segments, executes the LLM generation query,
        and logs performance indicators.
        """
        start_time = time.time()

        if not retrieved_chunks:
            return {
                "answer": "I do not have enough information to answer that based on the provided documents.",
                "citations": [],
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Format context segments
        context_str_list = []
        citations = []
        for idx, item in enumerate(retrieved_chunks):
            doc = item["document"]
            meta = doc.metadata
            context_str_list.append(
                f"[Segment {idx + 1}] Source: {meta.get('filename')}, Page: {meta.get('page_number')}, Chunk: {meta.get('chunk_number')}\n"
                f"Content: {doc.page_content}\n"
            )
            citations.append({
                "filename": meta.get("filename"),
                "file_path": meta.get("file_path"),
                "page_number": meta.get("page_number"),
                "chunk_number": meta.get("chunk_number"),
                "similarity_score": item.get("score", 0.0)
            })

        context_blocks = "\n---\n".join(context_str_list)
        formatted_sys_prompt = RAG_SYSTEM_PROMPT.format(context=context_blocks)

        # Call LLM Service
        logger.info("Invoking LLM for RAG answer generation...")
        llm_start = time.time()
        answer = self.llm_service.generate_response(formatted_sys_prompt, f"Question: {query}")
        llm_latency_ms = round((time.time() - llm_start) * 1000, 2)
        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(f"RAG Chain execution finished (LLM latency: {llm_latency_ms}ms, Total: {total_latency_ms}ms)")

        return {
            "answer": answer.strip(),
            "citations": citations,
            "latency_ms": total_latency_ms
        }
