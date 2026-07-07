import unittest
from tools.browser.browser_service import BrowserService, SimpleHTMLParser
from tools.browser.browser_utils import is_valid_url

class TestBrowserService(unittest.TestCase):
    def setUp(self):
        self.service = BrowserService()

    def test_utils(self):
        self.assertTrue(is_valid_url("http://google.com"))
        self.assertTrue(is_valid_url("https://localhost:8000/docs"))
        self.assertFalse(is_valid_url("ftp://google.com"))
        self.assertFalse(is_valid_url("google.com"))

    def test_html_parser(self):
        html = """
        <html>
            <head><title>Test Title</title></head>
            <body>
                <a href="https://example.com/one">Link One</a>
                <a href="/two">Link Two</a>
                <img src="/image.png" />
                <p>Hello World text</p>
                <script>console.log("script block");</script>
            </body>
        </html>
        """
        parser = SimpleHTMLParser()
        parser.feed(html)
        
        self.assertEqual(parser.title, "Test Title")
        self.assertEqual(len(parser.links), 2)
        self.assertEqual(parser.links[0]["url"], "https://example.com/one")
        self.assertEqual(parser.links[0]["text"], "Link One")
        self.assertEqual(len(parser.images), 1)
        self.assertEqual(parser.images[0], "/image.png")
        self.assertIn("Hello World text", parser.text_parts)
        self.assertNotIn('console.log("script block")', parser.text_parts)

    def test_search_and_read(self):
        results = self.service.google_search("python")
        self.assertTrue(len(results) > 0)
        
        content = self.service.read_page("https://example.com")
        self.assertEqual(content.url, "https://example.com")

if __name__ == "__main__":
    unittest.main()
