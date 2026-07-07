from fastapi import APIRouter

router = APIRouter()

@router.get("/chat")
def chat():
    return {
        "response": "Hello! I am Echo AI."
    }

