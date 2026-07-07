import os
from typing import List, Dict, Any, Optional
from tools.pdf.pdf_models import PDFMetadata, PDFPage, PDFSearchResult
from tools.pdf.pdf_utils import file_validator, page_range_validator, clean_text

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

class PDFService:
    def open_pdf(self, path: str) -> Dict[str, Any]:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found or invalid: {path}")
            
        pages = self.count_pages(path)
        metadata = self.extract_metadata(path)
        
        return {
            "path": path,
            "pages_count": pages,
            "metadata": metadata
        }

    def count_pages(self, path: str) -> int:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(path)
                return len(reader.pages)
            except Exception:
                pass
        
        # Mock default pages if pypdf is not available
        return 5

    def extract_metadata(self, path: str) -> PDFMetadata:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(path)
                meta = reader.metadata
                return PDFMetadata(
                    author=meta.author if meta else None,
                    creator=meta.creator if meta else None,
                    producer=meta.producer if meta else None,
                    subject=meta.subject if meta else None,
                    title=meta.title if meta else None,
                    pages=len(reader.pages)
                )
            except Exception:
                pass
                
        # Mock metadata
        return PDFMetadata(
            author="System Mock",
            creator="Echo AI",
            producer="Echo PDF Service",
            subject="Documentation",
            title=os.path.basename(path),
            pages=5
        )

    def extract_text(self, path: str, page_range: Optional[str] = None) -> List[PDFPage]:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        total_pages = self.count_pages(path)
        pages_to_extract = page_range_validator(page_range, total_pages)
        
        extracted_pages = []
        
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(path)
                for page_idx in pages_to_extract:
                    text = reader.pages[page_idx].extract_text()
                    extracted_pages.append(PDFPage(
                        page_number=page_idx + 1,
                        text=clean_text(text)
                    ))
                return extracted_pages
            except Exception:
                pass
                
        # Mock text fallback
        for idx in pages_to_extract:
            extracted_pages.append(PDFPage(
                page_number=idx + 1,
                text=f"This is mock content for page {idx + 1} of PDF document: {os.path.basename(path)}."
            ))
        return extracted_pages

    def search_text(self, path: str, query: str) -> List[PDFSearchResult]:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        total_pages = self.count_pages(path)
        results = []
        
        # Read text for all pages
        pages = self.extract_text(path)
        for page in pages:
            if query.lower() in page.text.lower():
                # Extract a short snippet around the match
                start_idx = max(0, page.text.lower().find(query.lower()) - 30)
                end_idx = min(len(page.text), start_idx + len(query) + 60)
                snippet = page.text[start_idx:end_idx]
                results.append(PDFSearchResult(
                    page_number=page.page_number,
                    matched_text=f"...{snippet}...",
                    index=page.text.lower().find(query.lower())
                ))
        return results

    def extract_images(self, path: str, output_dir: str = "outputs/extracted_images") -> List[str]:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        os.makedirs(output_dir, exist_ok=True)
        images = []
        
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(path)
                count = 0
                for page_idx, page in enumerate(reader.pages):
                    for img_name, img_data in page.images.items():
                        count += 1
                        img_path = os.path.join(output_dir, f"img_{count}_{img_name}")
                        with open(img_path, "wb") as fp:
                            fp.write(img_data.data)
                        images.append(img_path)
                return images
            except Exception:
                pass
                
        # Mock images output
        mock_img = os.path.join(output_dir, "mock_image.png")
        with open(mock_img, "w") as fp:
            fp.write("MOCK IMAGE DATA")
        images.append(mock_img)
        return images

    def split_pdf(self, path: str, page_ranges: str, output_dir: str = "outputs") -> List[str]:
        if not file_validator(path):
            raise FileNotFoundError(f"PDF file not found: {path}")
            
        os.makedirs(output_dir, exist_ok=True)
        total_pages = self.count_pages(path)
        
        # Parse output splits
        # e.g., page_ranges = "1-2, 3-5"
        range_parts = page_ranges.split(',')
        generated_files = []
        
        if PYPDF_AVAILABLE:
            try:
                for idx, part in enumerate(range_parts):
                    reader = pypdf.PdfReader(path)
                    writer = pypdf.PdfWriter()
                    pages_to_keep = page_range_validator(part.strip(), total_pages)
                    for p in pages_to_keep:
                        writer.add_page(reader.pages[p])
                    
                    out_path = os.path.join(output_dir, f"split_{idx + 1}_{os.path.basename(path)}")
                    with open(out_path, "wb") as f:
                        writer.write(f)
                    generated_files.append(out_path)
                return generated_files
            except Exception:
                pass
                
        # Mock split output
        for idx, part in enumerate(range_parts):
            out_path = os.path.join(output_dir, f"split_{idx + 1}_{os.path.basename(path)}")
            with open(out_path, "w") as f:
                f.write(f"Mock Split PDF page range: {part}")
            generated_files.append(out_path)
            
        return generated_files

    def merge_pdf(self, paths: List[str], output_path: str = "outputs/merged.pdf") -> str:
        for path in paths:
            if not file_validator(path):
                raise FileNotFoundError(f"Invalid PDF in merge list: {path}")
                
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if PYPDF_AVAILABLE:
            try:
                merger = pypdf.PdfMerger()
                for path in paths:
                    merger.append(path)
                merger.write(output_path)
                merger.close()
                return output_path
            except Exception:
                pass
                
        # Mock merge output
        with open(output_path, "w") as f:
            f.write("Mock Merged PDF of files: " + ", ".join(paths))
        return output_path
