# PDF Tool

Provides PDF reading, extraction, searching and document analysis.

## Features

- **Open PDF**: Load PDF information.
- **Count Pages**: Retrieve total number of pages.
- **Extract Text**: Get text from specific page ranges.
- **Extract Metadata**: View document properties.
- **Search Text**: Look up keywords within pages.
- **Extract Images**: Extract embedded images.
- **Split PDF**: Split a document into parts.
- **Merge PDF**: Merge multiple documents.

## Endpoints

- `GET /pdf/pages`: Fetch PDF metadata and page count.
- `GET /pdf/text`: Extract text with page ranges.
- `GET /pdf/search`: Search keywords inside the document.
- `POST /pdf/split`: Split PDF by range.
- `POST /pdf/merge`: Merge multiple PDFs.
