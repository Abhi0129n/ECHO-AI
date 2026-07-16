from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CreateExcelRequest(BaseModel):
    path: str = Field(..., description="Destination path for the Excel file (.xlsx)")
    data: Dict[str, List[List[Any]]] = Field(..., description="Dictionary mapping sheet names to 2D lists of cell values")

class WordParagraph(BaseModel):
    text: str = Field(..., description="Paragraph text content")
    is_heading: bool = Field(default=False, description="Whether this paragraph is a heading")
    heading_level: int = Field(default=1, description="Heading level (1-9)")

class CreateWordRequest(BaseModel):
    path: str = Field(..., description="Destination path for the Word document (.docx)")
    title: str = Field(..., description="Document title")
    content: List[WordParagraph] = Field(..., description="List of paragraphs and headings")

class SlideContent(BaseModel):
    title: str = Field(..., description="Slide title")
    content: str = Field(..., description="Slide bullet points or body text (use newlines to separate points)")

class CreatePPTRequest(BaseModel):
    path: str = Field(..., description="Destination path for the PowerPoint file (.pptx)")
    title: str = Field(..., description="Presentation title slide title")
    subtitle: Optional[str] = Field(None, description="Presentation title slide subtitle")
    slides: List[SlideContent] = Field(..., description="List of presentation slides")

class ReadCSVRequest(BaseModel):
    path: str = Field(..., description="Path to the CSV file to read")
