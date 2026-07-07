from fastapi import FastAPI

from backend.routers.chat import router as chat_router
from tools.filesystem.filesystem_router import router as filesystem_router
from tools.notes.notes_router import router as notes_router
from tools.pdf.pdf_router import router as pdf_router
from tools.excel.excel_router import router as excel_router
from tools.system.system_router import router as system_router
from tools.gmail.gmail_router import router as gmail_router
from tools.calendar.calendar_router import router as calendar_router
from tools.browser.browser_router import router as browser_router

app = FastAPI(
    title="Echo AI",
    version="1.0.0"
)

app.include_router(chat_router)
app.include_router(filesystem_router)
app.include_router(notes_router)
app.include_router(pdf_router)
app.include_router(excel_router)
app.include_router(system_router)
app.include_router(gmail_router)
app.include_router(calendar_router)
app.include_router(browser_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to Echo AI Backend!"
    }