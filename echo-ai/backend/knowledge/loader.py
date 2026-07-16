import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, CSVLoader, BSHTMLLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_file_type(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    elif ext == ".csv":
        return "csv"
    elif ext in (".html", ".htm"):
        return "html"
    elif ext == ".md":
        return "markdown"
    elif ext == ".json":
        return "json"
    elif ext in (".py", ".js", ".ts", ".sh", ".bat", ".cpp", ".c", ".h", ".java", ".css"):
        return "code"
    return "txt"

class DocumentLoader:
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "500"))
        self.chunk_overlap = chunk_overlap or int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # Load splitter strategy separators
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def load_and_split(self, file_path: str) -> List[Document]:
        """
        Loads document using appropriate LangChain loader, splits content into chunks,
        and enriches each chunk with metadata.
        """
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        file_type = get_file_type(ext)
        filename = os.path.basename(file_path)

        # File timestamps in ISO format
        ctime = datetime.fromtimestamp(os.path.getctime(file_path), timezone.utc).isoformat()
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path), timezone.utc).isoformat()

        # Generate standard UUID5 from file path
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file_path))

        # Select Loader
        if file_type == "pdf":
            loader = PyPDFLoader(file_path)
            raw_docs = loader.load()
        elif file_type == "docx":
            loader = Docx2txtLoader(file_path)
            raw_docs = loader.load()
        elif file_type == "csv":
            loader = CSVLoader(file_path)
            raw_docs = loader.load()
        elif file_type == "html":
            loader = BSHTMLLoader(file_path)
            raw_docs = loader.load()
        else:
            loader = TextLoader(file_path, encoding="utf-8")
            raw_docs = loader.load()

        # Split into chunks
        chunks = self.splitter.split_documents(raw_docs)

        # Build clean enriched documents
        final_docs = []
        for idx, chunk in enumerate(chunks):
            page_num = chunk.metadata.get("page", 1)
            # Standardize 0-indexed PDF page outputs to 1-indexed for standard user citations
            if file_type == "pdf" and isinstance(page_num, int):
                page_num += 1

            chunk_meta = {
                "filename": filename,
                "file_path": file_path,
                "document_id": document_id,
                "file_type": file_type,
                "page_number": page_num,
                "chunk_number": idx + 1,
                "created_time": ctime,
                "modified_time": mtime
            }
            final_docs.append(Document(page_content=chunk.page_content, metadata=chunk_meta))

        return final_docs
