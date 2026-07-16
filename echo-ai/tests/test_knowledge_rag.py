import os
import shutil
import uuid
import pytest
import gc
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.embeddings.embedder import LocalEmbedder
from backend.vectorstore.faiss_store import FAISSStoreManager
from backend.knowledge.indexer import DocumentIndexer
from backend.knowledge.loader import DocumentLoader
from backend.memory.long_term import LongTermMemory
from tools.knowledge.router import get_knowledge_service
from tools.knowledge.service import KnowledgeService

@pytest.fixture
def temp_env_setup():
    """Sets up temporary workspace folders inside the project boundary for testing RAG index and DBs."""
    # Place temporary directory inside project root to ensure is_safe_path checks pass
    temp_dir_name = f"_test_temp_{uuid.uuid4().hex[:8]}"
    tmpdir = os.path.abspath(temp_dir_name)
    os.makedirs(tmpdir, exist_ok=True)
    
    index_path = os.path.join(tmpdir, "test_faiss_index")
    metadata_path = os.path.join(tmpdir, "test_kb_metadata.json")
    memory_index_path = os.path.join(tmpdir, "test_memory_index")
    db_path = os.path.join(tmpdir, "test_echo_ai.db")
    
    # Override environment variables
    with patch.dict(os.environ, {
        "FAISS_INDEX_PATH": index_path,
        "METADATA_PATH": metadata_path,
        "ENABLE_AUTO_INDEX": "True"
    }):
        yield {
            "tmpdir": tmpdir,
            "index_path": index_path,
            "metadata_path": metadata_path,
            "memory_index_path": memory_index_path,
            "db_path": db_path
        }
        
    # Clean resources
    gc.collect()
    if os.path.exists(tmpdir):
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass

@pytest.fixture
def client(temp_env_setup):
    with TestClient(app) as c:
        yield c

# ----------------- Loaders & Embeddings Tests -----------------

def test_embedder_local():
    embedder = LocalEmbedder()
    query = "test query"
    embedding = embedder.embed_query(query)
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert isinstance(embedding[0], float)

def test_loader_text_splitting(temp_env_setup):
    tmpdir = temp_env_setup["tmpdir"]
    txt_file = os.path.join(tmpdir, "sample.txt")
    
    # Write sample content (longer than chunk size to trigger split)
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("Line one content of the document.\n" * 100)
        
    loader = DocumentLoader(chunk_size=100, chunk_overlap=10)
    chunks = loader.load_and_split(txt_file)
    
    assert len(chunks) > 1
    assert chunks[0].metadata["filename"] == "sample.txt"
    assert chunks[0].metadata["file_type"] == "txt"
    assert chunks[0].metadata["chunk_number"] == 1

# ----------------- FAISS & Indexer Tests -----------------

def test_faiss_save_load_delete(temp_env_setup):
    index_path = temp_env_setup["index_path"]
    embedder = LocalEmbedder()
    faiss_mgr = FAISSStoreManager(index_path=index_path, embeddings=embedder)
    
    from langchain_core.documents import Document
    docs = [
        Document(page_content="Segment information content A", metadata={"filename": "docA.txt", "file_path": "docA.txt"}),
        Document(page_content="Segment information content B", metadata={"filename": "docB.txt", "file_path": "docB.txt"})
    ]
    
    chunk_ids = faiss_mgr.add_documents(docs)
    assert len(chunk_ids) == 2
    
    # Load in new manager to test persistence
    faiss_mgr_reloaded = FAISSStoreManager(index_path=index_path, embeddings=embedder)
    assert faiss_mgr_reloaded.vectorstore is not None
    
    # Test delete
    success = faiss_mgr_reloaded.delete_documents([chunk_ids[0]])
    assert success is True
    
    # Check that deleted key is no longer in docstore
    assert chunk_ids[0] not in faiss_mgr_reloaded.vectorstore.docstore._dict
    assert chunk_ids[1] in faiss_mgr_reloaded.vectorstore.docstore._dict

# ----------------- Hybrid Search & Citations Tests -----------------

def test_hybrid_search(temp_env_setup):
    index_path = temp_env_setup["index_path"]
    embedder = LocalEmbedder()
    faiss_mgr = FAISSStoreManager(index_path=index_path, embeddings=embedder)
    
    from langchain_core.documents import Document
    docs = [
        Document(page_content="Semantic routing details of virtual memory architecture.", metadata={"file_path": "os.txt", "file_type": "txt", "chunk_number": 1}),
        Document(page_content="Keywords search matching deadlock locks recovery.", metadata={"file_path": "db.txt", "file_type": "txt", "chunk_number": 1})
    ]
    faiss_mgr.add_documents(docs)
    
    from backend.knowledge.search import HybridSearcher
    searcher = HybridSearcher(faiss_mgr)
    
    # Test semantic similarity + keyword match
    results = searcher.search("virtual memory", k=1)
    assert len(results) == 1
    assert "virtual memory" in results[0]["document"].page_content
    
    # Test path filtering
    results_filtered = searcher.search("banana", file_path_filter="os.txt")
    assert len(results_filtered) == 0

# ----------------- Knowledge Tool Endpoint & Summarize Tests -----------------

@patch("backend.ai.llm.LLMService.generate_response")
def test_knowledge_tool_endpoints(mock_llm, client, temp_env_setup):
    mock_llm.return_value = "Retrieved RAG summary of deadlock structures."
    tmpdir = temp_env_setup["tmpdir"]
    
    doc_path = os.path.join(tmpdir, "deadlock.txt")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("Operating systems resolve deadlocks via avoidance and recovery algorithms.")
        
    # 1. Index document
    res = client.post("/knowledge/index", json={"file_path": doc_path})
    assert res.status_code == 200
    assert res.json()["status"] == "indexed"
    
    # 2. List documents
    res_list = client.get("/knowledge/list")
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1
    assert res_list.json()[0]["filename"] == "deadlock.txt"
    
    # 3. Search document
    res_search = client.post("/knowledge/search", json={"query": "How are deadlocks resolved?"})
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert "citations" in search_data
    assert len(search_data["citations"]) == 1
    assert search_data["citations"][0]["filename"] == "deadlock.txt"
    
    # 4. Summarize document
    res_sum = client.post("/knowledge/summarize", json={"file_path": doc_path})
    assert res_sum.status_code == 200
    assert "summary" in res_sum.json()

# ----------------- Auto Indexing via File Tool Tests -----------------

def test_file_tool_auto_indexing_trigger(client, temp_env_setup):
    tmpdir = temp_env_setup["tmpdir"]
    src_file = os.path.join(tmpdir, "source.txt")
    dest_file = os.path.join(tmpdir, "copied_dest.txt")
    
    with open(src_file, "w", encoding="utf-8") as f:
        f.write("Standard file text info indexed on copy trigger.")
        
    # Trigger File copy command via REST route
    res_copy = client.post("/file/copy", json={"src_path": src_file, "dest_path": dest_file})
    assert res_copy.status_code == 200
    
    # Verify file was auto-indexed into KB registry
    res_kb = client.get("/knowledge/list")
    assert res_kb.status_code == 200
    assert any(rec["filename"] == "copied_dest.txt" for rec in res_kb.json())

# ----------------- Long-Term Memory Database & Vector Search Tests -----------------

def test_long_term_memory_flow(temp_env_setup):
    db_path = temp_env_setup["db_path"]
    memory_index_path = temp_env_setup["memory_index_path"]
    
    memory = LongTermMemory(db_path=db_path, index_path=memory_index_path)
    
    # Add memories
    memory.add_memory(category="preference", key="preferred_model", value="llama-70b")
    memory.add_memory(category="style", key="indentation", value="Uses 4 spaces tab width")
    
    # List memories
    all_mem = memory.list_memories()
    assert len(all_mem) == 2
    
    # Semantic similarity memory lookup
    search_res = memory.search_memories("How should code be indented?", limit=1)
    assert len(search_res) == 1
    assert search_res[0]["key"] == "indentation"
    assert search_res[0]["value"] == "Uses 4 spaces tab width"
    
    # Delete memory
    memory.delete_memory(search_res[0]["id"])
    assert len(memory.list_memories()) == 1
