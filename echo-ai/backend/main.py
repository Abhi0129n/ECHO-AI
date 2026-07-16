from fastapi import FastAPI

from backend.chat.router import router as chat_router
from tools.filesystem.router import router as filesystem_router
from tools.notes.router import router as notes_router
from tools.pdf.router import router as pdf_router
from tools.productivity.router import router as productivity_router
from tools.system.router import router as system_router
from tools.gmail.router import router as gmail_router
from tools.calendar.router import router as calendar_router
from tools.browser.router import router as browser_router
from tools.knowledge.router import router as knowledge_router
from backend.core.logging_middleware import LoggingMiddleware

app = FastAPI(
    title="Echo AI",
    version="1.0.0"
)

app.add_middleware(LoggingMiddleware)

app.include_router(chat_router)
app.include_router(filesystem_router)
app.include_router(notes_router)
app.include_router(pdf_router)
app.include_router(productivity_router)
app.include_router(system_router)
app.include_router(gmail_router)
app.include_router(calendar_router)
app.include_router(browser_router)
app.include_router(knowledge_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to Echo AI Backend!"
    }