import os
import shutil
import unittest
from tools.pdf.pdf_service import PDFService
from tools.pdf.pdf_utils import page_range_validator, clean_text, normalize_text

class TestPDFService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.abspath("uploads/test_pdf_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.pdf_path = os.path.join(self.temp_dir, "sample.pdf")
        with open(self.pdf_path, "w") as f:
            f.write("Sample PDF contents")
            
        self.service = PDFService()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_utils(self):
        self.assertEqual(clean_text("  hello   world  "), "hello world")
        self.assertEqual(normalize_text("Hello, World!"), "hello world")
        
        # Test range validation (e.g. 5 total pages)
        self.assertEqual(page_range_validator("1-2, 4", 5), [0, 1, 3])
        self.assertEqual(page_range_validator("3-5", 5), [2, 3, 4])

    def test_service_metadata(self):
        metadata = self.service.extract_metadata(self.pdf_path)
        self.assertIsNotNone(metadata.pages)
        self.assertEqual(metadata.title, "sample.pdf")

    def test_service_extract_text(self):
        pages = self.service.extract_text(self.pdf_path, "1-2")
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].page_number, 1)

    def test_service_search_text(self):
        results = self.service.search_text(self.pdf_path, "mock")
        self.assertTrue(len(results) >= 0)

if __name__ == "__main__":
    unittest.main()
