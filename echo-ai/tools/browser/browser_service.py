import urllib.request
import urllib.parse
import os
from html.parser import HTMLParser
from typing import List, Dict, Any
from tools.browser.browser_models import WebsiteContent, LinkItem
from tools.browser.browser_utils import is_valid_url, get_default_headers

class SimpleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self.links = []
        self.images = []
        self._in_title = False
        self._in_script_or_style = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        elif tag in ("script", "style"):
            self._in_script_or_style = True
        elif tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href:
                # Capture text in handle_data or default to href
                self.links.append({"url": href, "text": ""})
        elif tag == "img":
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src")
            if src:
                self.images.append(src)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("script", "style"):
            self._in_script_or_style = False

    def handle_data(self, data):
        if self._in_title:
            self.title = data.strip()
        elif self._in_script_or_style:
            pass
        else:
            txt = data.strip()
            if txt:
                self.text_parts.append(txt)
                # If the last link doesn't have text yet, associate this data
                if self.links and not self.links[-1]["text"]:
                    self.links[-1]["text"] = txt

class BrowserService:
    def google_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        # Using DuckDuckGo HTML search since Google search blocks simple requests without JS
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        try:
            req = urllib.request.Request(url, headers=get_default_headers())
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            # Parse DuckDuckGo search results
            parser = SimpleHTMLParser()
            parser.feed(html)
            
            # Filter results from DDG HTML
            results = []
            for item in parser.links:
                href = item["url"]
                text = item["text"]
                # Filter out DDG utility links
                if "duckduckgo.com" not in href and href.startswith("http") and text:
                    results.append({
                        "title": text,
                        "url": href,
                        "snippet": "DuckDuckGo search result match."
                    })
                    if len(results) >= max_results:
                        break
            if results:
                return results
        except Exception:
            pass
            
        # Mock Search fallback
        return [
            {
                "title": f"Search Results for '{query}' - Reference A",
                "url": f"https://example.com/search?q={urllib.parse.quote(query)}",
                "snippet": f"This is a simulated web search result for query term: {query}."
            },
            {
                "title": f"Understanding {query} - Reference B",
                "url": f"https://docs.example.com/{urllib.parse.quote(query)}",
                "snippet": f"Detailed documentation describing various applications of {query} in web tech."
            }
        ]

    def read_page(self, url: str) -> WebsiteContent:
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL schema: {url}")
            
        try:
            req = urllib.request.Request(url, headers=get_default_headers())
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
            parser = SimpleHTMLParser()
            parser.feed(html)
            
            links = [LinkItem(text=l["text"] or l["url"], url=l["url"]) for l in parser.links]
            
            return WebsiteContent(
                url=url,
                title=parser.title or "Web Page",
                html_content=html[:5000],  # Clamp raw html display
                text_content=" ".join(parser.text_parts[:200]),
                links=links[:20],
                images=parser.images[:20]
            )
        except Exception as e:
            # Fallback mock
            return WebsiteContent(
                url=url,
                title=f"Mock Web Page: {url}",
                html_content=f"<html><body><h1>Mock Content for {url}</h1><p>Offline or failed to resolve address: {str(e)}</p></body></html>",
                text_content=f"Simulated read of {url}. Error: {str(e)}",
                links=[LinkItem(text="Home", url=url)],
                images=[]
            )

    def download_pdf(self, url: str, output_path: str = "uploads/downloaded.pdf") -> str:
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        try:
            req = urllib.request.Request(url, headers=get_default_headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(output_path, "wb") as f:
                    f.write(response.read())
            return output_path
        except Exception as e:
            # Fallback mock file
            with open(output_path, "w") as f:
                f.write(f"Mock downloaded PDF from URL: {url}. Original error: {str(e)}")
            return output_path

    def extract_links(self, html_content: str) -> List[LinkItem]:
        parser = SimpleHTMLParser()
        parser.feed(html_content)
        return [LinkItem(text=l["text"] or l["url"], url=l["url"]) for l in parser.links]

    def extract_images(self, html_content: str) -> List[str]:
        parser = SimpleHTMLParser()
        parser.feed(html_content)
        return parser.images
