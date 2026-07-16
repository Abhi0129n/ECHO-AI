from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from tools.knowledge.schemas import IndexRequest, DeleteRequest, SearchRequest, SearchResponse, SummarizeRequest
from tools.knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()

@router.post("/index", status_code=status.HTTP_200_OK)
def index_document(request: IndexRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        return service.index_document(request.file_path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/delete", status_code=status.HTTP_200_OK)
def delete_document(request: DeleteRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        success = service.delete_document(request.file_path)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Document '{request.file_path}' not registered in index."
            )
        return {"success": True, "message": "Document deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        res = service.search(
            query=request.query,
            file_path_filter=request.file_path_filter,
            file_type_filter=request.file_type_filter
        )
        return SearchResponse(
            answer=res["answer"],
            citations=res["citations"],
            latency_ms=res["latency_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/list", response_model=List[Dict[str, Any]])
def list_documents(service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        return service.list_documents()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/reindex", status_code=status.HTTP_200_OK)
def reindex(service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        return service.reindex()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/summarize", status_code=status.HTTP_200_OK)
def summarize_document(request: SummarizeRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    try:
        summary = service.summarize_document(request.file_path)
        return {"file_path": request.file_path, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
